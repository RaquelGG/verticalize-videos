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
set "LAYOUT_MODE="
set "SIGMA_VALUE=5"
set "BLUR_VALUE=20"
set "ZOOM_VALUE=1.0"
set "OUTPUT_VIDEO="

:arg_loop
IF "%2"=="" GOTO :end_args
IF /I "%2"=="-layout" (
    set "LAYOUT_MODE=--layout"
    SHIFT
    GOTO :arg_loop
)
IF /I "%2"=="-s" (
    set "SIGMA_VALUE=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
IF /I "%2"=="-b" (
    set "BLUR_VALUE=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
IF /I "%2"=="-z" (
    set "ZOOM_VALUE=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
IF /I "%2"=="-o" (
    set "OUTPUT_VIDEO=%3"
    SHIFT
    SHIFT
    GOTO :arg_loop
)
SHIFT
GOTO :arg_loop

:end_args

set "SIGMA_ARG=--smooth-sigma %SIGMA_VALUE%"
set "BLUR_ARG=--blur %BLUR_VALUE%"
set "ZOOM_ARG=--zoom %ZOOM_VALUE%"

REM --- Set default output path if not provided ---
if not defined OUTPUT_VIDEO (
    if defined LAYOUT_MODE (
        set "OUTPUT_VIDEO=%INPUT_DIR%cropped_%~n1_layout.mp4"
    ) else (
        set "OUTPUT_VIDEO=%INPUT_DIR%cropped_%~n1.mp4"
    )
)

set "OUTPUT_ARG=--output "%OUTPUT_VIDEO%""

IF defined LAYOUT_MODE (
    echo --- Running in Layout Mode ---
    python "%PYTHON_SCRIPT%" --file "%VIDEO_FILE%" %LAYOUT_MODE% %BLUR_ARG% %ZOOM_ARG% %OUTPUT_ARG%
) ELSE (
    echo --- Running in Tracking Mode ---
    python "%PYTHON_SCRIPT%" --file "%VIDEO_FILE%" --output "%FFMPEG_SCRIPT%" %SIGMA_ARG%

    if %errorlevel% neq 0 (
        echo.
        echo Python script failed. Aborting.
        exit /b %errorlevel%
    )

    echo.
    echo --- Step 2: Running ffmpeg to create the cropped video ---
    ffmpeg -y -i "%VIDEO_FILE%" -filter_complex_script "%FFMPEG_SCRIPT%" -map "[outv]" -map "[outa]" "%OUTPUT_VIDEO%"
)

if %errorlevel% neq 0 (
    echo.
    echo ffmpeg command failed.
    exit /b %errorlevel%
)

echo.
echo --- Done! ---
echo Cropped video created at: %OUTPUT_VIDEO%
