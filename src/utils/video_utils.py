from os import listdir, path, mkdir
import cv2
from PyQt6.QtWidgets import QProgressBar


def video_crop(video_path: str, video_index: int, out_dir: str, progress: QProgressBar):
    cap = cv2.VideoCapture(video_path)

    cnt = 0

    w_frame, h_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps, frames = cap.get(cv2.CAP_PROP_FPS), cap.get(cv2.CAP_PROP_FRAME_COUNT)

    h, w = int(h_frame / 2), int(w_frame / 3)

    sections = []
    for i in range(6):
        x, y = (i % 3)*w, (i // 3)*h
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(
            f'{out_dir}/{video_index}_{i}.avi', fourcc, fps, (w, h), True)
        sections.append((x, y, out))

    while (cap.isOpened()):
        ret, frame = cap.read()

        cnt += 1

        if ret == False:
            break

        xx = int(cnt * 100 / frames)
        progress.setValue(xx)
        print(f'{int(xx)}%')

        for (x, y, out) in sections:
            crop_frame = frame[y:y+h, x:x+w]

            out.write(crop_frame)

    cap.release()
    for (_, _, out) in sections:
        out.release()
    cv2.destroyAllWindows()


def process_videos(srcs_dir: str, progress: QProgressBar):
    out_dir = f'{srcs_dir}/.out'

    # already processed
    if path.exists(out_dir):
        return

    mkdir(out_dir)
    videos = list(filter(lambda s: not s.startswith('.'), listdir(srcs_dir)))
    for i in range(len(videos)):
        video_path = f'{srcs_dir}/{videos[i]}'
        video_crop(video_path, i, out_dir, progress)
