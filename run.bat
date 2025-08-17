@echo off
set "VIDEO_FILE=%1"
if not defined VIDEO_FILE (
    echo Usage: run.bat ^<path_to_video_file^>
    exit /b 1
)

set "PYTHON_SCRIPT=crop_video.py"
set "FFMPEG_SCRIPT=videos/output.txt"

set "OUTPUT_VIDEO=%2"
if not defined OUTPUT_VIDEO (
    set "OUTPUT_VIDEO=videos/cropped_%~n1.mp4"
)

echo --- Step 1: Running Python script to generate ffmpeg filter script ---
python %PYTHON_SCRIPT% --file "%VIDEO_FILE%" --output "%FFMPEG_SCRIPT%"

if %errorlevel% neq 0 (
    echo.
    echo Python script failed. Aborting.
    exit /b %errorlevel%
)

echo.
echo --- Step 2: Running ffmpeg to create the cropped video ---
ffmpeg -i "%VIDEO_FILE%" -filter_complex_script "%FFMPEG_SCRIPT%" -map "[outv]" -map "[outa]" "%OUTPUT_VIDEO%"

if %errorlevel% neq 0 (
    echo.
    echo ffmpeg command failed.
    exit /b %errorlevel%
)

echo.
echo --- Done! ---
echo Cropped video created at: %OUTPUT_VIDEO%
