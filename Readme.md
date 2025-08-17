# Video Object Tracker and Cropper

This project provides a Python script to track a selected object in a video and generate an FFmpeg script to create a new, cropped vertical video that keeps the object in the center of the frame.

## How to Use

### For Windows Users (Easy Way)

A `run.bat` script is provided to automate the entire process.

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the script:**
    Open a command prompt, navigate to the project directory, and run:
    ```bash
    run.bat "path\\to\\your_video.mp4"
    ```
    -   Replace `"path\\to\\your_video.mp4"` with the full path to your video file. Make sure to enclose the path in quotes if it contains spaces.

    -   An interactive window will open for you to select the object to track.
    -   The final cropped video will be saved in the `videos/` directory with the name `cropped_your_video.mp4`.

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

### Optional Arguments

You can customize the script's behavior with these optional arguments:

-   `--output <filename>`: Specifies a different name for the generated ffmpeg script (default is `output.txt`).
-   `--tracker <tracker_name>`: Choose a different OpenCV tracking algorithm. Options are `csrt` (default), `kcf`, or `mil`.
-   `--smooth-sigma <value>`: Adjusts the smoothness of the camera motion (default is `5`). A higher value results in smoother, less jerky movement.

Example with optional arguments:
```bash
python crop_video.py --file my_video.mp4 --output my_script.txt --smooth-sigma 10
```