# Python Editor for LazyVidEditor

This directory contains Python scripts used for video editing, audio processing, and subtitle generation as part of the LazyVidEditor project.

## Scripts

-   **`scenetest_friday.py` (and similar `scenetest_*.py` files):**
    -   The main Python-based video editing script.
    -   Uses the `moviepy` library to perform edits.
    -   Relies on scene timestamps parsed from an OBS log file (`C:\Users\glencroftplay\AppData\Roaming\obs-studio\logs\infowriterlog.txt`).
    -   Capabilities include loading video clips, subclipping based on scenes, compositing camera and slide footage, applying effects (masking, opacity), adding image overlays (logos), and rendering final videos.
    -   Currently falls back to manual user input for video synchronization.

-   **`autosub_app.py`:**
    -   A command-line tool to automatically generate subtitles for video/audio files.
    -   Extracts audio using `ffmpeg`.
    -   Uses the Google Speech API (and optionally Google Translate API via `google-api-python-client`) for speech-to-text and translation.
    -   Formats the output into subtitle files (e.g., SRT).
    -   Note: This script appears to be written for Python 2.7.

-   **`alignment_by_row_channels.py`:**
    -   Implements an audio fingerprinting algorithm to determine the time delay (synchronization) between two video files.
    -   It extracts audio, performs FFT analysis, and compares frequency peaks to find the offset.
    -   This script is intended for automated video synchronization but is currently not actively used by `scenetest_friday.py` due to noted performance/accuracy issues.

-   **`pyaudioeditsinit.py`:**
    -   A script for extracting audio from video files using `ffmpeg`.
    -   Includes an option for audio compression using `ffmpeg`'s `compand` filter.
    -   Appears to be an initial or utility script for audio processing tasks.

-   **`infowriterlog.txt`:**
    -   This is not a script, but a sample log file, likely from OBS, that `scenetest_friday.py` might use (or used to use) to get scene information. The primary OBS log path for scene timings is hardcoded in `scenetest_friday.py`.

## Dependencies

The Python scripts rely on several libraries and external tools:

**Python Packages:**
-   `moviepy`: For core video editing functionalities.
-   `google-api-python-client`: For accessing Google APIs (Speech-to-Text, Translate) in `autosub_app.py`.
-   `requests`: For making HTTP requests, used by `autosub_app.py`.
-   `scipy`: For numerical operations, specifically `scipy.io.wavfile` used in `alignment_by_row_channels.py`.
-   `numpy`: A dependency for `scipy` and potentially `moviepy`, used for numerical array manipulations.
-   `progressbar`: Used in `autosub_app.py` to display command-line progress.
-   Pillow (`PIL`): Used for image manipulation, often a dependency of `moviepy`.
-   `timecode`: For working with video timecodes in `scenetest_friday.py`.

Standard Python libraries are also used (e.g., `os`, `sys`, `argparse`, `json`, `subprocess`).

**External Tools:**
-   `ffmpeg`: Essential for audio extraction (used by `autosub_app.py`, `pyaudioeditsinit.py`, `alignment_by_row_channels.py`) and video rendering (via `moviepy`). Must be installed and in the system's PATH.
-   `imagemagick` (`convert` command): Used by `scenetest_friday.py` for image manipulation tasks like cropping and resizing preview PNGs. Must be installed and in the system's PATH for these features to work.

**Note:** `autosub_app.py` appears to be written for Python 2.x (e.g., uses `print` without parentheses, `xrange`). Other scripts like `scenetest_friday.py` might use Python 3 syntax or be compatible with both, but this should be verified.
