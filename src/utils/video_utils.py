from typing import Generator
from os import listdir, path, mkdir
import cv2
from statistics import mode

SUPPORTED_TYPES = ['mp4', 'mkv']


def check_video_type(filename: str) -> bool:
    ext = filename.split('.')[-1]
    return ext in SUPPORTED_TYPES


class VideoWriter:
    __multiple: bool = None
    __writer: cv2.VideoWriter | list[cv2.VideoWriter] = None

    __codec = cv2.VideoWriter_fourcc(*'MJPG')
    __ext: str = 'avi'

    __path: str = None
    __fps: float = None

    def __init__(self, out_dir: str, video_index: int, fps: float, crop: bool) -> None:
        self.__path = f'{out_dir}/{video_index}'
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
    h_frame, w_frame, _ = frame.shape
    h, w = int(h_frame / 2) - 1, int(w_frame / 3) - 1
    sections = []
    for i in range(6):
        x, y = (i % 3)*w, (i // 3)*h
        sections.append(frame[y:y+h, x:x+w])
    return sections


def reshape(frame, shape: tuple[int, int]):
    h_frame, w_frame, _ = frame.shape
    w_shape, h_shape = shape

    AR = w_frame / h_frame
    AR_shape = w_shape / h_shape

    new_shape = [w_frame, h_frame]

    if AR > AR_shape:  # horizontal image
        new_shape[0] = int(h_frame * AR_shape)
    elif AR < AR_shape:  # vertical image
        new_shape[1] = int(w_frame / AR_shape)

    return cv2.resize(frame, new_shape)


def process_video(video_path: str, video_index: int, out_dir: str, shape: tuple[int, int], fps: float, crop: bool) -> Generator[int, None, None]:
    # open video file
    cap = cv2.VideoCapture(video_path)

    # get video metadata
    w_frame, h_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    w_fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(
        cv2.CAP_PROP_FRAME_COUNT)

    if (w_frame != shape[0] or h_frame != shape[1]):
        print(
            f'[WARN] Video {video_index} is being resized to fit aspect ratio: {shape[0]} x {shape[1]}')

    # open writer for output video
    writer = VideoWriter(out_dir, video_index, w_fps, crop)

    # pass through each frame
    cnt = 0
    while (cap.isOpened()):
        # read the frame
        ret, frame = cap.read()
        if ret == False:
            break

        # compute how much is done
        cnt += 1
        xx = int(cnt * 100 / frames)
        yield xx

        # resize when needed
        frame = reshape(frame, shape)

        # crop video
        if (crop):
            cropped = crop_frame(frame)
            writer.write(cropped)
        else:
            writer.write(frame)

    # release resources
    cap.release()
    writer.release()


def process_videos(srcs_dir: str, auto_crop: bool) -> Generator[tuple[int, int], None, None]:
    # filter out unsopported file formats
    videos = list(filter(check_video_type, listdir(srcs_dir)))

    # send out total number of supported videos in srcs_dir
    total = len(videos)
    yield (0, total)

    # if an out_dir already exists, assume we are done and stop processing
    # TODO: how we check if processing is done
    out_dir = f'{srcs_dir}/.out'
    if path.exists(out_dir):
        yield (100, total)
        return

    # begin processing

    # make output directory
    mkdir(out_dir)

    # find "correct" aspect ratio
    metadata = []
    min_fps = 100
    for i in range(total):
        video_path = f'{srcs_dir}/{videos[i]}'
        cap = cv2.VideoCapture(video_path)
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        min_fps = min(min_fps, fps)
        metadata.append((w, h))
        cap.release()
    shape = mode(metadata)

    # crop videos into 6 quadrants
    count = 0
    for i in range(total):
        video_path = f'{srcs_dir}/{videos[i]}'
        for pct in process_video(video_path, i, out_dir, shape, min_fps, auto_crop):
            yield (pct, count)
        count += 1
        yield (pct, count)
