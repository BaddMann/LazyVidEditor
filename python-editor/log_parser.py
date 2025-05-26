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
                        # Invalid timestamp format, ignore this timestamp
                        line_content_after_ts = line # Process line without new timestamp
                        pass
                else:
                    line_content_after_ts = line # No timestamp on this line

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
                    # Attempt to parse the line (or relevant part) as JSON
                    # OBS logs can sometimes have other text on the line with JSON
                    # A simple heuristic: check if line starts with { and ends with }
                    potential_json_str = line_content_after_ts
                    if potential_json_str.startswith('{') and potential_json_str.endswith('}'):
                        obs_data = json.loads(potential_json_str)
                        if isinstance(obs_data, dict) and obs_data.get("update-type") == "SwitchScenes":
                            scene_name = obs_data.get("scene-name")
                            # Look for 'rec-timecode' or other common timecode fields
                            obs_timecode = obs_data.get("rec-timecode") # From Parse-badlog.ps1
                            if not obs_timecode: # Try other potential keys
                                obs_timecode = obs_data.get("timecode")
                            
                            event_data["event_type"] = "SceneChange"
                            event_data["details"] = {"scene_name": scene_name}
                            if obs_timecode:
                                event_data["details"]["obs_timecode"] = obs_timecode
                            parsed_events.append(event_data)
                            continue
                except json.JSONDecodeError:
                    # Not a valid JSON line, or not the JSON we're looking for
                    pass
                
                # 5. Extron Video Matrix Changes (Conceptual - Omitted for now as per instruction)
                # If specific reliable patterns for Extron are identified, they can be added here.
                # Example:
                # if line_content_after_ts.startswith("Evt"):
                #     # Further parsing for specific Extron event details
                #     event_data["event_type"] = "ExtronEvent"
                #     event_data["details"] = {"extron_info": "some parsed data"}
                #     parsed_events.append(event_data)
                #     continue

    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

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
