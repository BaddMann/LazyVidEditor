# Audio Event Integration Concept for LazyVidEditor

This document outlines a conceptual approach for integrating audio analysis events (from `audio_analyzer.py`) with the primary log events (from `log_parser.py`) to create a comprehensive, multi-layered event timeline for LazyVidEditor.

## Goal

The primary goal is to enrich the editing decision-making process by correlating external system events (mic mutes, scene changes) with detailed audio events (speaker activity, sound types like silence/speech/music, or potentially specific trained sounds like 'piano' or 'singing' in the future).

## 1. Establishing a Common Timeline

A crucial step is to align all events onto a single, absolute timeline.

*   **Video Zero Point (Reference Timestamp):**
    *   The main video file (e.g., camera recording) needs a "zero point" timestamp that corresponds to an absolute time in the main log.
    *   This could be:
        1.  The timestamp of a "RecordingStart" event captured by `log_parser.py` if this event reliably marks the actual start of the video recording.
        2.  The file creation/modification time of the primary video file, if it's known to be closely synchronized with the start of the logging process. (Less reliable).
        3.  A manually inserted "sync marker" event in the logs at the very beginning of a recording session (e.g., triggered by a visual/audio cue like a clapper).
    *   Let's call this `T_video_zero_abs`.

*   **Converting Audio Event Timings:**
    *   `audio_analyzer.py` currently outputs event start/end times in seconds *relative to the start of the analyzed audio/video file*.
    *   To place these on the absolute timeline:
        *   `event_abs_start_time = T_video_zero_abs + timedelta(seconds=event_relative_start_sec)`
        *   `event_abs_end_time = T_video_zero_abs + timedelta(seconds=event_relative_end_sec)`
    *   These absolute datetime objects can then be compared/sorted with events from `log_parser.py`.

## 2. Proposed Master Event List Structure

A "master event list" would be a chronological list of all events from all sources. Each event could be a dictionary with a common structure, plus type-specific details:

```python
# Example Event Structure
{
    'timestamp_start_dt': datetime_object,  # Absolute start time (for point events, end_dt might be same or None)
    'timestamp_end_dt': datetime_object,    # Absolute end time (for duration events)
    'source_script': 'log_parser' / 'audio_analyzer', # Origin of the event
    'event_type': 'MicMute' / 'SceneChange' / 'SpeakerSegment' / 'SoundSegment' / 'ExtronEvent' / etc.,
    'duration_sec': float, # Duration in seconds for interval events
    'details': {
        # Type-specific details
        # e.g., for MicMute: {'mic_name': 'Input 1 Mute', 'state': 'muted'}
        # e.g., for SpeakerSegment: {'speaker_id': 'S1'}
        # e.g., for SoundSegment: {'segment_type': 'sound' / 'silence'}
        # e.g., for SceneChange: {'scene_name': 'Main Camera'}
    },
    'original_log_line': "...", # Optional: the raw log line if applicable
    'line_number': "..." # Optional: line number from original log
}
```

## 3. Merging Process (Conceptual)

1.  Parse the main log file using `log_parser.py` to get system events (already has absolute `raw_timestamp`).
2.  Identify the primary video file associated with the log.
3.  Determine `T_video_zero_abs` for this video file (this might require some heuristics or manual input if a "RecordingStart" event isn't perfectly aligned).
4.  Run `audio_analyzer.py` on the primary video file.
5.  Convert the relative event times from `audio_analyzer.py` to absolute datetimes using `T_video_zero_abs`.
6.  Combine the two lists of events.
7.  Sort the combined list chronologically based on `timestamp_start_dt`.

## 4. Enabling More Sophisticated Editing Decisions

This merged timeline allows for more complex queries and logic:

*   **Find segments where "Mic X is unmuted" AND "Speaker A is active (from diarization)" AND "segment_type is 'sound' (not silence)".**
    *   This would provide much cleaner vocal segments.
*   **Identify all slides (`SceneChange` events) presented while "Speaker B" was talking.**
*   **Flag parts of the recording where "Music" is detected (if a music classifier was available) and no one is speaking.**
    *   Useful for identifying sections to replace with higher quality audio or for copyright checks.
*   **Correlate Extron events (e.g., a specific source selected) with periods of speech from a particular microphone.**
*   **If piano/singing detection were added:** "Show all segments where 'piano' was detected during a 'worship' scene."

## 5. Integration with Editing Scripts

*   **`scenetest_friday.py` / `ffmpeg_command_generator.py`:**
    *   These scripts would need to be modified to accept this master event list (or a derivative of it).
    *   Their segment generation logic (`generate_segments_from_events`) would be enhanced to use the richer event data for defining more precise or context-aware cuts.
    *   For example, instead of just cutting on MicMute/Unmute, it could look for the actual start/end of speech within that window using the diarization and sound/silence data.

## Challenges

*   **Accurate `T_video_zero_abs`:** The accuracy of the entire merged timeline depends heavily on correctly establishing the absolute start time of the video relative to the log events.
*   **Synchronization between different audio tracks (if any):** If audio for analysis comes from a different source than the main camera audio used for the final video, their relative sync (`secssync`) is still crucial. The audio analysis should ideally be performed on the audio track that will be used in the final edit, or one that is perfectly synced with it.
*   **Complexity of event correlation logic.**
*   **Performance of audio analysis for long videos.**

This conceptual framework provides a path towards a more intelligent and context-aware automated editing process for LazyVidEditor.
```
