from typing import Generator, Any
from os import listdir, path, mkdir
from threading import Thread, Event
import cv2
from statistics import mode
from fractions import Fraction

SUPPORTED_TYPES = ['mp4', 'mkv', 'avi']


def isSupported(filename: str) -> bool:
    ext = filename.split('.')[-1]
    return ext in SUPPORTED_TYPES


class VideoWriter:
    __multiple: bool = None
    __writer: cv2.VideoWriter | list[cv2.VideoWriter] = None

    __codec = cv2.VideoWriter_fourcc(*'MJPG')
    __ext: str = 'avi'

    __path: str = None
    __fps: float = None

    def __init__(self, out_dir: str, video: str, fps: float, crop: bool) -> None:
        self.__path = f'{out_dir}/{video}'
        self.__multiple = crop
        self.__fps = fps
        if (crop):
            self.__writer = [None for _ in range(6)]

    def get_writer(self, img, i=0):
        h, w, _ = img.shape
        if (self.__multiple):
            writer = self.__writer[i]
            if (writer is not None):
                return writer
            self.__writer[i] = cv2.VideoWriter(f'{self.__path}_{i}.{self.__ext}',
                                               self.__codec, self.__fps, (w, h), True)
            return self.__writer[i]
        else:
            if (self.__writer is not None):
                return self.__writer
            self.__writer = cv2.VideoWriter(
                f'{self.__path}.{self.__ext}', self.__codec, self.__fps, (w, h), True)
            return self.__writer

    def write(self, frame):
        if (self.__multiple):
            for i in range(6):
                writer = self.get_writer(frame[i], i)
                writer.write(frame[i])
        else:
            writer = self.get_writer(frame)
            writer.write(frame)

    def release(self):
        if (self.__multiple):
            for w in self.__writer:
                if (w is not None):
                    w.release()
        else:
            if (self.__writer is not None):
                self.__writer.release()


def crop_frame(frame) -> list:
    """Crops frame into 6 quadrants
    Takes a frame and returns a list of 6 frames"""

    h_frame, w_frame, _ = frame.shape
    h, w = int(h_frame / 2) - 1, int(w_frame / 3) - 1
    sections = []
    for i in range(6):
        x, y = (i % 3)*w, (i // 3)*h
        sections.append(frame[y:y+h, x:x+w])
    return sections


def transformShape(shape: tuple[int, int], ar: float):
    """Takes a (width, height) shape and a desired aspect ratio
    and returns a new shape, as close as possible to the original one
    but respecting the new aspect ratio"""

    w, h = shape
    old_ar = w / h

    new_shape = [w, h]
    if old_ar > ar:  # horizontal image
        new_shape[0] = int(h * ar)
    elif old_ar < ar:  # vertical image
        new_shape[1] = int(w / ar)
    return new_shape


def reshape(frame, shape: tuple[int, int]):
    """Returns a new frame, resized to fit the aspect ratio
    of the given shape"""

    h_frame, w_frame, _ = frame.shape
    w_shape, h_shape = shape

    AR_shape = w_shape / h_shape

    new_shape = transformShape((w_frame, h_frame), AR_shape)

    return cv2.resize(frame, new_shape)

def findNumberOfFrames(frame: int, fps: float, new_fps: float) -> int:
    """Returns the number of times the frame should be written to fit the new fps"""

    ratio = fps / new_fps
    if (ratio > 1):
        return int(frame % round(ratio) == 0)
    return round(1 / ratio)
    
    


class VideoMetadata():
    total: int = 0
    frame_counts: list[int] = []
    sizes: list[tuple[int, int]] = []
    width: int = 0
    height: int = 0
    fps: float = 0

    def __init__(self, total: int, frame_counts: list[int], sizes: list[tuple[int, int]], w: int, h: int, fps: float):
        self.total = total
        self.frame_counts = frame_counts
        self.sizes = sizes
        self.width = w
        self.height = h
        self.fps = fps


class ProcessingUpdateMessage():
    frames_done: list[int] = None
    metadata: VideoMetadata = None
    message_general: str = ''
    messages: list[str] = None
    elapsed_time: int = None

    modified: Event = Event()

    def __init__(self, total: int, metadata: VideoMetadata) -> None:
        self.frames_done = [0 for _ in range(total)]
        self.messages = ['' for _ in range(total)]
        self.metadata = metadata

    def set_message(self, msg: str, index: int = None) -> None:
        if (index is None):
            changed = self.message_general != msg
            if changed:
                self.modified.set()
            self.message_general = msg
            return
        changed = self.messages[index] != msg
        if changed:
            self.modified.set()
        self.messages[index] = msg

    def set_frames(self, frame: int, index: int) -> None:
        changed = self.frames_done[index] != frame
        if changed:
            self.modified.set()
        self.frames_done[index] = frame

    def message(self) -> str:
        msg = self.message_general
        if (msg != ''):
            self.message_general = ''
            return msg
        for i in range(len(self.messages)):
            msg = self.messages[i]
            if (msg != ''):
                self.messages[i] = ''
                return msg
        return ''

    def wait(self):
        self.modified.wait()
        self.modified.clear()

    def done(self):
        self.modified.set()


def process_video(dir_path: str, video: str, video_index: int, out_dir: str,
                  shape: tuple[int, int], fps: float, 
                  resize: bool, crop: bool, adjust_fps: bool,
                  update: ProcessingUpdateMessage) -> None:
    # open video file
    video_path = f'{dir_path}/{video}'
    cap = cv2.VideoCapture(video_path)

    # get video metadata
    w_frame, h_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w_fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(
        cv2.CAP_PROP_FRAME_COUNT)

    ar = w_frame / h_frame
    ar_shape = shape[0] / shape[1]
    ar_fract = Fraction(shape[0], shape[1])
    if (resize and (ar != ar_shape)):
        update.set_message(
            f'Video {video} will be resized to fit aspect ratio {ar_fract.numerator}:{ar_fract.denominator}', video_index)

    # open writer for output video
    video_name = '.'.join(video.split('.')[:-1])
    writer = VideoWriter(
        out_dir,
        f'{video_index}' if crop else video_name,
        fps,
        crop
    )

    # pass through each frame
    cnt = 0
    while (cap.isOpened()):
        # read the frame
        ret, frame = cap.read()
        if ret == False:
            break

        # resize when needed
        if (resize):
            frame = reshape(frame, shape)

        # crop video when needed
        if (crop):
            frame = crop_frame(frame)

        n = 1
        if (adjust_fps):
            n = findNumberOfFrames(cnt, w_fps, fps)

        for _ in range(n):
            writer.write(frame)

        # compute how much is done
        cnt += 1
        update.set_frames(cnt, video_index)

    # release resources
    cap.release()
    writer.release()
    update.done()


def find_metadata(srcs_dir: str, crop: bool) -> tuple[VideoMetadata, str]:
    dir = listdir(srcs_dir)
    supported = list(filter(isSupported, dir))

    unsupported = list(filter(lambda x: not isSupported(x), dir))
    unsupported_files = ', '.join(unsupported)
    msg = ''
    if (len(unsupported) > 0):
        msg = f'The following files are not supported and will be ignored:\n{unsupported_files}'

    # get total number of supported videos in srcs_dir
    total = len(supported)

    if (total == 0):
        return (None, msg)

    # find metadata
    aspects = []
    frame_counts = []
    min_fps = 100
    max_shape = (0, 0)
    for i in range(total):
        video_path = f'{srcs_dir}/{supported[i]}'
        cap = cv2.VideoCapture(video_path)

        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(
            cv2.CAP_PROP_FRAME_COUNT)

        if (w > max_shape[0] or h > max_shape[1]):
            max_shape = (w, h)
        min_fps = min(min_fps, fps)
        aspects.append((w, h))
        frame_counts.append(frames)

        cap.release()

    common_shape = mode(aspects)
    target_ar = common_shape[0] / common_shape[1]
    shape = transformShape(max_shape, target_ar)

    # send initial metadata
    t = total if crop else int(total / 6)
    w = shape[0] if crop else 3 * shape[0]
    h = shape[1] if crop else 2 * shape[1]
    metadata = VideoMetadata(t, frame_counts, aspects, w, h, min_fps)
    return (metadata, msg)


def process_videos(srcs_dir: str, resize: bool, crop: bool, adjust_fps: bool) -> Generator[ProcessingUpdateMessage, None, None]:
    # filter out unsopported file formats
    dir = listdir(srcs_dir)
    videos = list(filter(isSupported, dir))

    # get total number of supported videos in srcs_dir
    total = len(videos)

    # send out initial metadata
    metadata, msg = find_metadata(srcs_dir, crop)
    update = ProcessingUpdateMessage(total, metadata)
    update.set_message(msg)

    yield update

    # begin processing
    skip = not resize and not crop and not adjust_fps
    if (skip or total == 0):
        yield update
        return

    # if an out_dir already exists, assume we are done and stop processing
    # TODO: how we check if processing is done
    out_dir = f'{srcs_dir}/.out'
    if path.exists(out_dir):
        update.set_message('Videos have already been processed')
        yield update
        return

    # make output directory
    mkdir(out_dir)

    # process each video
    shape = (metadata.width, metadata.height)
    threads: list[Thread] = []
    for i in range(total):
        t = Thread(target=process_video, args=[
            srcs_dir, videos[i], i, out_dir, shape, metadata.fps, resize, crop, adjust_fps, update])
        t.start()
        threads.append(t)

    running = True
    while (running):
        update.wait()
        yield update
        running = threads_running(threads)


def threads_running(threads: list[Thread]):
    for t in threads:
        if (t.is_alive()):
            return True
    return False
