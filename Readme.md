# Video Object Tracker and Cropper

This project provides a Python script to track a selected object in a video and generate an FFmpeg script to create a new, cropped vertical video that keeps the object in the center of the frame.

## Modes of Operation

This script has two main modes:

1.  **Tracking Mode (Default):** Tracks a selected object in a video and generates a cropped video that keeps the object centered.
2.  **Layout Mode:** Creates a vertical video with the original video centered, and a blurred, scaled-up version in the background.

---

## How to Use

### For Windows Users (Easy Way)

A `run.bat` script is provided to automate the entire process. First, install dependencies:
```bash
pip install -r requirements.txt
```

**To use Tracking Mode:**
```bash
run.bat "path\\to\\your_video.mp4" [/s sigma_value] [/o "path\\to\\output.mp4"]
```
-   This is the default mode.
-   An interactive window will open for you to select the object to track.

**To use Layout Mode:**
```bash
run.bat "path\\to\\your_video.mp4" /layout [/b blur_amount] [/z zoom_factor] [/o "path\\to\\output.mp4"]
```
-   The `/layout` flag is required to enable this mode.
-   `/b blur_amount`: (Optional) Sets the background blur amount (e.g., `/b 30`). Defaults to 20.
-   `/z zoom_factor`: (Optional) Sets the zoom level for the foreground video (e.g., `/z 1.2` for a 20% zoom). Defaults to 1.0 (no zoom).

**Common Arguments for `run.bat`:**
-   `"path\\to\\your_video.mp4"`: The full path to your video file (required).
-   `/o "path\\to\\output.mp4"`: (Optional) The path where the final video will be saved.
-   `/s sigma_value`: (Optional, Tracking Mode only) Controls camera smoothness.

**Note:** You can add the folder containing `run.bat` to your system's PATH environment variable. This will allow you to run the script from any directory in your command prompt.

---

### For All Users (Manual Steps)

The process involves two main stages:
1.  Running the Python script to track an object and generate a filter script.
2.  Using the `ffmpeg` command-line tool with the generated script to create the final cropped video.

#### Step 1: Install Dependencies

First, you need to install the required Python libraries. Open your terminal or command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

#### Step 2: Run the Tracking Script

Next, run the `crop_video.py` script. You must provide the path to your input video file.

```bash
python crop_video.py --file videos/your_video.mp4
```

-   An interactive window will open showing the first frame of your video.
-   Use your mouse to draw a box around the object you want to track.
-   Once you are satisfied with the box, press the `ENTER` or `SPACE` key.

The script will then automatically process the rest of the video. When it's finished, a file named `videos/output.txt` will be created.

#### Step 3: Create the Cropped Video with FFmpeg

Now, use the generated script with `ffmpeg` to perform the actual cropping. Run the following command in your terminal:

```bash
ffmpeg -i videos/your_video.mp4 -filter_complex_script videos/output.txt -map "[outv]" -map "[outa]" videos/cropped_video.mp4
```

-   Replace `videos/your_video.mp4` with the path to your original video.
-   The output script is `videos/output.txt` by default.
-   Replace `videos/cropped_video.mp4` with your desired output file name.

---

### Python Script Arguments (`crop_video.py`)

You can customize the script's behavior with these optional arguments:

-   `--layout`: Use layout mode instead of tracking.
-   `--output <filename>`: In tracking mode, specifies the name for the generated ffmpeg script. In layout mode, specifies the name of the final output video.
-   `--tracker <tracker_name>`: (Tracking mode) Choose a different OpenCV tracking algorithm. Options are `csrt` (default), `kcf`, or `mil`.
-   `--smooth-sigma <value>`: (Tracking mode) Adjusts the smoothness of the camera motion (default is `5`).
-   `--blur <value>`: (Layout mode) Adjusts the blur amount for the background (default is `20`).
-   `--zoom <value>`: (Layout mode) Sets the zoom factor for the foreground video (default is `1.0`).

Example with tracking mode:
```bash
python crop_video.py --file my_video.mp4 --output my_script.txt --smooth-sigma 10
```

Example with layout mode:
```bash
python crop_video.py --file my_video.mp4 --layout --blur 30 --zoom 1.2 --output my_layout_video.mp4
```