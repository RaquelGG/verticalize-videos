@echo off
set "VIDEO_FILE=%1"
if not defined VIDEO_FILE (
    echo Usage: run.bat ^<path_to_video_file^>
    exit /b 1
)

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%crop_video.py"
set "INPUT_DIR=%~dp1"
set "FFMPEG_SCRIPT=%INPUT_DIR%output.txt"

REM --- Parse named arguments ---
set "SIGMA_VALUE=5"
set "OUTPUT_VIDEO=%INPUT_DIR%cropped_%~n1.mp4"

:arg_loop
IF "%2"=="" GOTO :end_args
IF /I "%2"=="/s" (
    set "SIGMA_VALUE=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
IF /I "%2"=="/o" (
    set "OUTPUT_VIDEO=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
SHIFT
GOTO :arg_loop

:end_args

set "SIGMA_ARG=--smooth-sigma %SIGMA_VALUE%"

echo --- Step 1: Running Python script to generate ffmpeg filter script ---
python "%PYTHON_SCRIPT%" --file "%VIDEO_FILE%" --output "%FFMPEG_SCRIPT%" %SIGMA_ARG%

if %errorlevel% neq 0 (
    echo.
    echo Python script failed. Aborting.
    exit /b %errorlevel%
)

echo.
echo --- Step 2: Running ffmpeg to create the cropped video ---
ffmpeg -y -i "%VIDEO_FILE%" -filter_complex_script "%FFMPEG_SCRIPT%" -map "[outv]" -map "[outa]" "%OUTPUT_VIDEO%"

if %errorlevel% neq 0 (
    echo.
    echo ffmpeg command failed.
    exit /b %errorlevel%
)

echo.
echo --- Done! ---
echo Cropped video created at: %OUTPUT_VIDEO%
