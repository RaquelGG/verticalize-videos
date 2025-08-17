import cv2
import argparse
import imutils
import numpy as np
from scipy.ndimage import gaussian_filter1d
import subprocess
import os

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

def create_layout_video(args):
    input_file = args["file"]
    output_file = args["output"]
    blur_amount = args["blur"]
    zoom_factor = args["zoom"]

    # Get video dimensions
    vs = cv2.VideoCapture(input_file)
    frame_height = int(vs.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(vs.get(cv2.CAP_PROP_VIDEO_WIDTH))
    vs.release()

    # Assuming a 9:16 vertical output
    output_width = 1080
    output_height = 1920

    if frame_width > frame_height: # Horizontal video
        bg_scale = f"scale=-1:{output_height}"
        fg_scale = f"scale={int(output_width * zoom_factor)}:-1"
    else: # Vertical or square video
        bg_scale = f"scale={output_width}:-1"
        fg_scale = f"scale=-1:{int(output_height * zoom_factor)}"


    filter_complex = (
        f"[0:v]split[fg_pre][bg_pre];"
        f"[bg_pre]{bg_scale},crop={output_width}:{output_height},boxblur={blur_amount}:1[bg];"
        f"[fg_pre]{fg_scale}[fg];"
        f"[bg][fg]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[outv]"
    )

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a?", # Map audio if it exists
        "-c:a", "copy",
        output_file
    ]

    print("Running ffmpeg command:")
    print(" ".join(ffmpeg_command))

    subprocess.run(ffmpeg_command, check=True)
    print(f"Layout video created at: {output_file}")


def create_tracking_video(args):
    vs = cv2.VideoCapture(args["file"])
    fps = vs.get(cv2.CAP_PROP_FPS)
    frame_height = int(vs.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(vs.get(cv2.CAP_PROP_VIDEO_WIDTH))

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

    output_script_path = args["output"]
    with open(output_script_path, "w") as file:
        file.write(filter_complex)

    print(f"FFmpeg script written to {output_script_path}")
    print(f"Now run: ffmpeg -y -i {args['file']} -filter_complex_script {output_script_path} -map \"[outv]\" -map \"[outa]\" path/to/cropped_video.mp4")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="path to input video file")

    # --- Modes ---
    ap.add_argument("--layout", action="store_true", help="Use layout mode instead of tracking.")

    # --- Tracking Mode Arguments ---
    ap.add_argument("-o", "--output", default="output.txt", help="Path for script (tracking mode) or final video (layout mode).")
    ap.add_argument("-t", "--tracker", type=str, default="csrt", help="OpenCV object tracker type.")
    ap.add_argument("-r", "--ratio", type=int, default=5, help="Ratio to resize frames for processing.")
    ap.add_argument("-s", "--smooth-sigma", type=int, default=5, help="Sigma for gaussian smoothing.")

    # --- Layout Mode Arguments ---
    ap.add_argument("-b", "--blur", type=int, default=20, help="Blur amount for the background in layout mode.")
    ap.add_argument("-z", "--zoom", type=float, default=1.0, help="Zoom factor for the foreground video in layout mode.")

    args = vars(ap.parse_args())

    if args["layout"]:
        # In layout mode, the --output argument is the final video file
        input_path = args["file"]
        # Default output path for layout mode
        if args["output"] == "output.txt":
             args["output"] = f"{os.path.splitext(input_path)[0]}_layout.mp4"
        create_layout_video(args)
    else:
        create_tracking_video(args)

if __name__ == "__main__":
    main()
