# LazyVidEditor - Python GUI Concept

This document outlines a conceptual design for a simple Graphical User Interface (GUI) for the Python-based components of the LazyVidEditor.
The goal is to provide an easier way to interact with the log parsing and video editing scripts.

## Proposed Technology

A simple web-based GUI using **Flask** or **Streamlit** (Python libraries) could be a good approach for rapid development and cross-platform accessibility. Alternatively, a desktop application using **Tkinter** (built-in Python) or **PyQt** could be considered. For this concept, we'll lean towards a web-based approach for simplicity in demonstration.

## Core UI Elements and Workflow

The GUI would be laid out in a step-by-step manner:

**1. Log File Input:**
    *   **UI Element:** File picker button ("Select Log File (`*-Slides.txt`)").
    *   **Action:** User selects one of the `*-Slides.txt` log files.
    *   **Display:** Shows the selected log file path.
    *   **Button:** "Parse Log File"

**2. Log Parsing and Event Display:**
    *   **Action:** User clicks "Parse Log File". The backend calls `log_parser.py`'s `parse_log_file` function.
    *   **UI Element:** A scrollable text area or table to display key events from the log.
    *   **Display Columns (example for a table):**
        *   Timestamp
        *   Event Type (MicMute, MicUnmute, SceneChange, RecordingStart, etc.)
        *   Details (e.g., Mic Name, Scene Name)
    *   **Filtering (Optional Enhancement):** Dropdown to filter event types.

**3. Video File Inputs:**
    *   **UI Element:** Two file picker buttons:
        *   "Select Camera Video File"
        *   "Select Slides Video File"
    *   **Display:** Shows selected video file paths.
    *   **Configuration Note:** The GUI could also display/allow editing of key paths from `editor_config.json` here (e.g., logo path, output directory).

**4. Editing Options / Triggering Edits:**
    *   **Context:** This section would be linked to the events displayed in step 2. For example, the user could select a "MicUnmute" event from the table.
    *   **UI Elements (per selected event or for a general action):**
        *   Input field for "Segment Title/Name" (defaults based on event).
        *   Dropdown for "Presentation Style" (from `scenetest_friday.py`: Overlay, Title, Lower Third).
        *   Input fields for manual start/end time overrides (if needed, otherwise use event timings).
        *   Button: "Generate Video Segment"
    *   **Action:**
        *   When "Generate Video Segment" is clicked, the backend would trigger a simplified version of the `scenetest_friday.py`'s `quickedit` logic.
        *   It would use the selected log event's timing (or manual overrides), the chosen video files, and presentation style.
    *   **Feedback:** Display progress (e.g., "Processing...") and a success/failure message with the path to the output video.

**5. Batch Processing (Future Enhancement):**
    *   Option to select multiple microphone segments or scene changes and batch-process them with default settings.

## Backend Logic (Conceptual)

*   The Python GUI framework (Flask/Streamlit) would handle HTTP requests.
*   Routes/callbacks would:
    *   Invoke `log_parser.parse_log_file(selected_log_path)`.
    *   Invoke relevant functions from `scenetest_friday.py` (likely needing some refactoring in `scenetest_friday.py` to be more easily callable with specific parameters rather than its current script flow).
    *   Manage file paths and configuration settings (reading from `editor_config.json`).

## Visual Layout Sketch (Text-based)

```
-----------------------------------------------------
| LazyVidEditor Control Panel                       |
-----------------------------------------------------
| Step 1: Select Log File                           |
| [Choose `*-Slides.txt` File]  [Selected: ____ ]   |
| [Parse Log File]                                  |
-----------------------------------------------------
| Step 2: Review Events                             |
| Filter: [All Events ▼]                            |
| | Timestamp           | Event Type | Details    | |
| |---------------------|------------|------------| |
| | 2023-10-27 10:01:00 | MicUnmute  | Input 1    | |
| | ...                 | ...        | ...        | |
|                                                   |
-----------------------------------------------------
| Step 3: Select Video Files                        |
| Camera: [Choose *.mp4 File]   [Selected: ____ ]   |
| Slides: [Choose *.mp4 File]   [Selected: ____ ]   |
-----------------------------------------------------
| Step 4: Generate Edit (based on selected event)   |
| Event: MicUnmute - Input 1 at 10:01:00            |
| Title: [Default_Title_Mic1        ]               |
| Style: [Overlay ▼]                                |
| [Generate Video Segment]                          |
-----------------------------------------------------
| Output Log / Status:                              |
| Processing segment...                             |
| Segment 'Default_Title_Mic1.mp4' created.         |
-----------------------------------------------------
```

## Simplifications for Initial Version

*   Focus on a single selected event triggering a single video generation.
*   Use default settings from `editor_config.json` extensively.
*   Error handling displayed simply in the status area.

This conceptual design aims to provide a user-friendly way to leverage the existing Python scripts' power.
