import re
import json
from datetime import datetime
import argparse
import pprint

# Regex for timestamps YYYY-MM-DD HH:MM:SS
TIMESTAMP_REGEX = re.compile(r"^\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})")

# Regex for Q-SYS mic mute/unmute events
# Example: cv "Input 1 Mute" "muted"
Q SYS_MIC_REGEX = re.compile(r'cv\s+"(Input\s\d+\sMute)"\s+"(muted|unmuted)"')

def parse_log_file(log_file_path):
    """
    Parses a log file to extract relevant events.

    Args:
        log_file_path (str): The path to the log file.

    Returns:
        list: A list of dictionaries, where each dictionary represents an event.
    """
    parsed_events = []
    last_timestamp_dt = None
    last_timestamp_str = ""

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # 1. Parse Timestamps
                timestamp_match = TIMESTAMP_REGEX.match(line)
                if timestamp_match:
                    current_timestamp_str = timestamp_match.group(1)
                    try:
                        current_timestamp_dt = datetime.strptime(current_timestamp_str, "%Y-%m-%d %H:%M:%S")
                        last_timestamp_dt = current_timestamp_dt
                        last_timestamp_str = current_timestamp_str
                        # Remove timestamp from line for further processing of the same line
                        line_content_after_ts = line[timestamp_match.end():].strip()
                    except ValueError:
                        # Invalid timestamp format on this line, use last known good timestamp
                        # The line content itself (line_content_after_ts) will be the full line
                        # for event checking.
                        print(f"Warning: Invalid timestamp format on line {line_number}: '{line}'. Using last known timestamp: {last_timestamp_str if last_timestamp_str else 'None'}.")
                        line_content_after_ts = line 
                else:
                    # No timestamp found at the beginning of this line.
                    # Use last known good timestamp and process the whole line for events.
                    line_content_after_ts = line

                # Prepare event_data with the last known valid timestamp
                event_data = {
                    "timestamp": last_timestamp_str,
                    "raw_timestamp": last_timestamp_dt,
                    "line_number": line_number,
                    "log_line": line,
                    "details": {}
                }

                # 2. Identify Recording Start/Stop
                if "RecordingStarting" in line_content_after_ts:
                    event_data["event_type"] = "RecordingStart"
                    parsed_events.append(event_data)
                    continue # Move to next line after identifying event
                elif "RecordingStopping" in line_content_after_ts:
                    event_data["event_type"] = "RecordingStop"
                    parsed_events.append(event_data)
                    continue

                # 3. Identify Q-SYS Microphone Mute/Unmute
                qsys_match = QSYS_MIC_REGEX.search(line_content_after_ts)
                if qsys_match:
                    mic_name = qsys_match.group(1)
                    state = qsys_match.group(2)
                    event_data["event_type"] = "MicUnmute" if state == "unmuted" else "MicMute"
                    event_data["details"] = {"mic_name": mic_name, "state": state}
                    parsed_events.append(event_data)
                    continue

                # 4. Identify OBS Scene Changes (JSON)
                try:
                    # Attempt to parse the line_content_after_ts as JSON
                    # Heuristic: check if it starts with '{' and ends with '}'
                    if line_content_after_ts.startswith('{') and line_content_after_ts.endswith('}'):
                        obs_data = json.loads(line_content_after_ts) # This line is inside the try-except
                        
                        update_type = obs_data.get("update-type")
                        if update_type == "SwitchScenes":
                            scene_name = obs_data.get("scene-name", "Unknown Scene")
                            if scene_name == "Unknown Scene":
                                print(f"Warning: 'scene-name' key missing in OBS SwitchScenes event on line {line_number}.")
                            
                            # Attempt to get rec-timecode or timecode
                            obs_timecode = obs_data.get("rec-timecode")
                            if obs_timecode is None: # If rec-timecode is not found or is null
                                obs_timecode = obs_data.get("timecode") # Try 'timecode'
                            
                            event_data["event_type"] = "SceneChange"
                            event_data["details"] = {"scene_name": scene_name}
                            if obs_timecode is not None: # Ensure obs_timecode is not None before adding
                                event_data["details"]["obs_timecode"] = obs_timecode
                            else:
                                print(f"Warning: Neither 'rec-timecode' nor 'timecode' found for OBS SwitchScenes event on line {line_number}.")
                                
                            parsed_events.append(event_data)
                            continue # Processed as OBS SceneChange, move to next line
                        # Add other OBS event types here if needed
                        # else:
                        #     print(f"Info: JSON object on line {line_number} is not a 'SwitchScenes' event: {line_content_after_ts}")

                except json.JSONDecodeError:
                    # This means line_content_after_ts started with { and ended with } but was not valid JSON
                    print(f"Warning: Could not parse potential JSON on line {line_number}: {line_content_after_ts}")
                    # Continue to check for other event types, as it might be a malformed JSON attempt
                    # or something else that coincidentally starts/ends with braces.
                
                # 5. Extron Video Matrix Changes
                # Check if the line (after timestamp removal) starts with "Evt" (case-insensitive)
                if line_content_after_ts.lower().startswith("evt"):
                    event_data["event_type"] = "ExtronEvent"
                    # Store the part of the line that starts with "Evt" as raw_event
                    event_data["details"] = {"raw_event": line_content_after_ts}
                    parsed_events.append(event_data)
                    continue # Processed as ExtronEvent, move to next line

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return []
    except PermissionError:
        print(f"Error: Permission denied when trying to read {log_file_path}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while processing {log_file_path} at line {line_number if 'line_number' in locals() else 'unknown'}: {e}")
        # Optionally, re-raise the exception if it's critical: raise
        return parsed_events # Return what has been parsed so far

    return parsed_events

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse log files for specific events.")
    parser.add_argument("log_file", help="Path to the log file to parse.")
    args = parser.parse_args()

    print(f"Parsing log file: {args.log_file}")
    events = parse_log_file(args.log_file)

    if events:
        print("\nParsed Events:")
        pprint.pprint(events)
    else:
        print("No events parsed or an error occurred.")

    # Example of how to sort by raw_timestamp if needed later
    # if events:
    #     events_sorted = sorted(events, key=lambda x: x['raw_timestamp'] if x['raw_timestamp'] else datetime.min)
    #     print("\nSorted Events:")
    #     pprint.pprint(events_sorted)
