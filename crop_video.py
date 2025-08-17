import cv2
import argparse
import imutils
import numpy as np
from scipy.ndimage import gaussian_filter1d

class Rectangle:
    final_width = 0
    final_height = 0

    def __init__(self, x1, x2, y1, y2, frame_number, ratio):
        self.x1 = float(x1)
        self.x2 = float(x2)
        self.y1 = float(y1)
        self.y2 = float(y2)
        self.frame_number = int(frame_number)
        self.ratio = float(ratio)

    @staticmethod
    def from_roi(roi, frame_number, ratio):
        return Rectangle(roi[0], roi[0] + roi[2], roi[1], roi[1] + roi[3], frame_number, ratio)

    def get_x1(self):
        return self.x1 * self.ratio

    def get_x2(self):
        return self.x2 * self.ratio

    def get_y1(self):
        return self.y1 * self.ratio

    def get_y2(self):
        return self.y2 * self.ratio

    def get_center_x(self):
        return int(((self.x1 + self.x2) / 2) * self.ratio)

    def get_point1_unscaled(self):
        return int(self.x1), int(self.y1)

    def get_point2_unscaled(self):
        return int(self.x2), int(self.y2)

    def get_frame_number(self):
        return self.frame_number

OPENCV_OBJECT_TRACKERS = {
    "csrt": cv2.TrackerCSRT.create,
    "kcf": cv2.TrackerKCF.create,
    "mil": cv2.TrackerMIL.create,
}

class RectangleTracker:

    def __init__(self, *, vs: cv2.VideoCapture, frame_width: int, file: str, ratio: float, tracker: str):
        self.file = file
        self.ratio = ratio
        self.vs = vs
        self.frame_width = frame_width
        self.total_frames = int(vs.get(cv2.CAP_PROP_FRAME_COUNT))
        self.tracker = OPENCV_OBJECT_TRACKERS[tracker]()

    def track(self) -> {int: Rectangle}:
        rectangles: {int: Rectangle} = {}
        roi_found = False
        cur_frame_number = 0

        self.vs.set(cv2.CAP_PROP_POS_FRAMES, 0)
        while cur_frame_number < self.total_frames:
            _, frame = self.vs.read()
            if frame is None:
                break

            resized_frame = imutils.resize(frame, width=int(self.frame_width / self.ratio))

            if not roi_found:
                roi = cv2.selectROI(self.file, resized_frame, fromCenter=False)
                rectangles[cur_frame_number] = Rectangle.from_roi(roi, cur_frame_number, self.ratio)
                self.tracker.init(resized_frame, roi)
                roi_found = True
            else:
                cur_frame_number += 1
                (roi_found, box) = self.tracker.update(resized_frame)
                if roi_found:
                    (x, y, w, h) = [int(v) for v in box]
                    cv2.rectangle(resized_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    rectangles[cur_frame_number] = Rectangle(x, x + w, y, y + h, cur_frame_number, self.ratio)

            cv2.putText(resized_frame, f"Frame: {cur_frame_number}/{self.total_frames}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow(self.file, resized_frame)
            cv2.waitKey(1) & 0xFF

        return rectangles

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="path to input video file")
    ap.add_argument("-o", "--output", type=str, default="videos/output.txt", help="path to output ffmpeg script")
    ap.add_argument("-t", "--tracker", type=str, default="csrt", help="OpenCV object tracker type")
    ap.add_argument("-r", "--ratio", type=int, default=5, help="ratio to resize frames for processing")
    ap.add_argument("-s", "--smooth-sigma", type=int, default=5, help="sigma for gaussian smoothing")
    args = vars(ap.parse_args())

    vs = cv2.VideoCapture(args["file"])
    fps = vs.get(cv2.CAP_PROP_FPS)
    frame_0 = vs.read()[1]
    frame_height, frame_width = frame_0.shape[:2]

    Rectangle.final_width = frame_height / 16 * 9
    Rectangle.final_height = frame_height

    tracker = RectangleTracker(vs=vs, frame_width=frame_width, file=args["file"], ratio=args["ratio"], tracker=args["tracker"])
    rectangles = tracker.track()

    vs.release()
    cv2.destroyAllWindows()

    if not rectangles:
        print("No objects tracked.")
        return

    centers = [rect.get_center_x() for num, rect in sorted(rectangles.items())]
    smoothed_centers = gaussian_filter1d(np.array(centers, dtype=float), sigma=args["smooth_sigma"])

    height = frame_height
    width = int(height * 9 / 16)

    video_filters = []
    audio_filters = []
    concat_inputs = ""

    for i, center_x in enumerate(smoothed_centers):
        x = int(center_x - width / 2)
        if x < 0:
            x = 0
        if x + width > frame_width:
            x = frame_width - width

        start_time = i / fps

        video_filters.append(f"[0:v]trim=start={start_time}:duration={1/fps},setpts=PTS-STARTPTS,crop={width}:{height}:{x}:0,format=yuv420p[v{i}]")
        audio_filters.append(f"[0:a]atrim=start={start_time}:duration={1/fps},asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs += f"[v{i}][a{i}]"

    filter_complex = ";".join(video_filters) + ";" + ";".join(audio_filters) + ";"
    filter_complex += f"{concat_inputs}concat=n={len(smoothed_centers)}:v=1:a=1[outv][outa]"

    with open(args["output"], "w") as file:
        file.write(filter_complex)

    print(f"FFmpeg script written to {args['output']}")
    print(f'Now run: ffmpeg -i {args["file"]} -filter_complex_script {args["output"]} -map "[outv]" -map "[outa]" videos/cropped_video.mp4')

if __name__ == "__main__":
    main()
