#import datetime
#from datetime import datetime
import os, fnmatch
from collections import defaultdict
import sys, getopt
#from PIL import Image
from datetime import datetime, timedelta, time as dt_time # Added time for combining with date
from subprocess import call
import json # Added for JSON configuration loading

#import ffmpy
from moviepy.editor import *
# from timecode import Timecode # Will be replaced by direct second calculations

# Imports for log_parser integration
from log_parser import parse_log_file
import pprint # For potentially pretty-printing parsed events if needed

# --- Configuration Loading ---
CONFIG_FILE = "editor_config.json" # Assumes config file is in the same directory
DEFAULT_CONFIG = {
    "video_search_path": "Z:", # Note: JSON uses double backslashes, Python strings can use single or double
    "obs_infowriter_log": "C:/Users/glencroftplay/AppData/Roaming/obs-studio/logs/infowriterlog.txt",
    "logo_bug_path": "Z:/glencroft-logo.png",
    "output_path_prefix": "./output/"
    # alignment_settings will be added below
}

DEFAULT_ALIGNMENT_SETTINGS = {
    "fft_bin_size": 1024,
    "overlap": 0,
    "box_height": 512,
    "box_width": 43,
    "samples_per_box": 7,
    "duration1_secs": 120,
    "duration2_secs": 60,
    "plausible_offset_threshold_secs": 600 
}

config = DEFAULT_CONFIG.copy() # Start with defaults
config['alignment_settings'] = DEFAULT_ALIGNMENT_SETTINGS.copy() # Add default alignment settings

try:
    # Try to determine the script's directory to make config file path more robust
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, CONFIG_FILE)
    with open(config_file_path, 'r') as f:
        loaded_file_config = json.load(f)
        config.update(loaded_file_config) # Update top-level keys
        # Specifically update alignment_settings if present in file, to merge nested dictionary
        if 'alignment_settings' in loaded_file_config:
            config['alignment_settings'].update(loaded_file_config['alignment_settings'])
    print(f"Loaded configuration from {config_file_path}")
except FileNotFoundError:
    print(f"Warning: {CONFIG_FILE} not found in {script_dir if 'script_dir' in locals() else 'current directory'}. Using default configuration.")
    # Optionally, create a default one:
    # script_dir_for_default = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else "."
    # default_config_path = os.path.join(script_dir_for_default, CONFIG_FILE)
    # try:
    #     with open(default_config_path, 'w') as f_default:
    #         json.dump(DEFAULT_CONFIG, f_default, indent=4)
    #     print(f"Created a default {default_config_path}. Please review it.")
    # except Exception as e:
    #     print(f"Could not create default config: {e}")
except json.JSONDecodeError:
    print(f"Error: Could not decode {CONFIG_FILE}. Using default configuration.")
except NameError: # __file__ might not be defined in some execution contexts
    print(f"Warning: Could not determine script directory to find {CONFIG_FILE}. Trying current directory.")
    try:
        with open(CONFIG_FILE, 'r') as f: # Fallback to current directory
            loaded_file_config_cwd = json.load(f)
            config.update(loaded_file_config_cwd) # Update top-level keys
            # Specifically update alignment_settings if present in file from CWD
            if 'alignment_settings' in loaded_file_config_cwd:
                config['alignment_settings'].update(loaded_file_config_cwd['alignment_settings'])
            print(f"Loaded configuration from {CONFIG_FILE} (current directory)")
    except FileNotFoundError:
        print(f"Warning: {CONFIG_FILE} not found in current directory. Using default configuration for all settings.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode {CONFIG_FILE} from current directory. Using default configuration for all settings.")


N = 1
today = datetime.today()
lastweek = datetime.today() - timedelta(days=N)
d = defaultdict(list)
#print today
Scenes = ["00:00:00"]
## List Files in the Arry Below if aiming For Specific Files. like this: "Z:\\2017-06-02-pm-Camera.mp4", "Z:\\2017-06-02-pm-Slides.mp4
Files = []
print Files


'''def main(argv):
   inputfile = ''
   outputfile = ''
   try:
      opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
   except getopt.GetoptError:
      print ('test.py -i <inputfile> -o <outputfile>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print ('test.py -i <inputfile> -o <outputfile>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputfile = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
   print ('Input file is ', inputfile)
   print ('Output file is ', outputfile)

if __name__ == "__main__":
   main(sys.argv[1:])'''


####Define Functions Here:
def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

#####Make this a Function...
def findscenes(thedate, obs_log_path):
    #fnd out how to set datetime object on function...
    #thedate = datetime.date.today()
    Scenes = []
    try:
        with open(os.path.normpath(obs_log_path)) as f:
            for line in f:
                #print line
                if thedate.strftime('%Y-%m-%d') in line:
                    if not Scenes:
                        Scenes.append("00:00:00")                
                    for line in f:  # now you are at the lines you want
                        if thedate.strftime('%Y-%m-%d') in line:
                            break
                        # do work
                        if 'Scene' in line:
                            fields = line.split('-')
                            #print fields
                            Scenes.append(fields[0].strip())
            return Scenes
    except FileNotFoundError:
        print(f"Error: OBS info writer log not found at {obs_log_path}. Returning empty scenes list.")
        return ["00:00:00"] # Return a default to prevent later errors if possible
    except Exception as e:
        print(f"Error reading OBS log {obs_log_path}: {e}. Returning empty scenes list.")
        return ["00:00:00"]

def userpromptssync(videosyncoutput):
    try:
        val = float(raw_input("Sync Seconds " +  str(videosyncoutput) + ": "))
        print("You entered", val)
        return val
    except ValueError:
        print("Invalid input. Please enter a number. Using 0.0 as default.") # Python 3 print
        return 0.0

# Refined userpromptssync
def userpromptssync(calculated_offset): # calculated_offset is now a float or None
    prompt_text = "Enter Sync Seconds (e.g., 2.5 if slides are 2.5s ahead of camera, -1.0 if camera is 1s ahead): "
    if calculated_offset is not None:
        prompt_text = f"Enter Sync Seconds (calculated: {calculated_offset:.2f}s, press Enter to use this value): "
    
    while True:
        try:
            # Use input() for Python 3
            user_input_str = input(prompt_text).strip()
            if not user_input_str and calculated_offset is not None:
                print(f"Using calculated offset: {calculated_offset:.2f}s")
                return calculated_offset
            val = float(user_input_str)
            print(f"User entered sync offset: {val:.2f}s")
            return val
        except ValueError:
            # This condition is tricky if calculated_offset is None and user enters nothing.
            # The above `if not user_input_str and calculated_offset is not None:` handles the primary case.
            # If user_input_str is empty AND calculated_offset is None, float() will raise ValueError.
            if not user_input_str and calculated_offset is None:
                 print("No input provided and no calculated offset available. Please enter a number.")
            else: # Input was non-empty but not a valid float
                print("Invalid input. Please enter a number (e.g., 3.5 or -2.0).")
        except EOFError: # Handle case where input stream is closed (e.g. script piped)
            if calculated_offset is not None:
                print(f"EOF reached. Using calculated offset: {calculated_offset:.2f}s")
                return calculated_offset
            print("EOF reached. No input provided and no calculated offset. Using offset 0.0s")
            return 0.0

# This function might be deprecated or changed if edits are fully automated
# def userpromptsslides(timecodes):
#     listofedits=[]
#     howmanyedits =  int(input("How Many edits are we performing? " )) # Py3 input
#     print(f"Editing {howmanyedits} times") # Py3 print
#     return listofedits

def VideoSynccall(video1, video2, alignment_config):
    import alignment_by_row_channels
    video1path = os.path.dirname(video1)
    video1file = os.path.basename(video1)
    video2file = os.path.basename(video2)
    
    align_params = alignment_config if isinstance(alignment_config, dict) else {}
    
    try:
        print(f"Calling alignment script for {video1file} and {video2file}...")
        print(f"Using alignment parameters: fft_bin_size={align_params.get('fft_bin_size', DEFAULT_ALIGNMENT_SETTINGS['fft_bin_size'])}, "
              f"duration1_secs={align_params.get('duration1_secs', DEFAULT_ALIGNMENT_SETTINGS['duration1_secs'])}, "
              f"duration2_secs={align_params.get('duration2_secs', DEFAULT_ALIGNMENT_SETTINGS['duration2_secs'])}")

        # alignment_by_row_channels.align returns a tuple (cam_ahead_by, slides_ahead_by)
        # one of the values is 0, the other is the offset.
        t = alignment_by_row_channels.align(
            video1file,
            video2file,
            video1path,
            fft_bin_size=align_params.get('fft_bin_size', DEFAULT_ALIGNMENT_SETTINGS['fft_bin_size']),
            overlap=align_params.get('overlap', DEFAULT_ALIGNMENT_SETTINGS['overlap']),
            box_height=align_params.get('box_height', DEFAULT_ALIGNMENT_SETTINGS['box_height']),
            box_width=align_params.get('box_width', DEFAULT_ALIGNMENT_SETTINGS['box_width']),
            samples_per_box=align_params.get('samples_per_box', DEFAULT_ALIGNMENT_SETTINGS['samples_per_box']),
            duration1_secs=align_params.get('duration1_secs', DEFAULT_ALIGNMENT_SETTINGS['duration1_secs']),
            duration2_secs=align_params.get('duration2_secs', DEFAULT_ALIGNMENT_SETTINGS['duration2_secs'])
        )

        if t is None: # If align script itself returns None (e.g. no pairs found in its internal logic)
             print("Warning: VideoSynccall received no valid offset tuple from alignment script.")
             return None

        # offset = slides_ahead_by - cam_ahead_by
        # If t = (cam_ahead, 0), offset = 0 - cam_ahead = -cam_ahead (negative, camera is ahead)
        # If t = (0, slides_ahead), offset = slides_ahead - 0 = slides_ahead (positive, slides are ahead)
        offset = t[1] - t[0] 
        
        plausible_threshold = align_params.get('plausible_offset_threshold_secs', DEFAULT_ALIGNMENT_SETTINGS['plausible_offset_threshold_secs'])
        
        print(f"Alignment script returned raw tuple: {t}, calculated offset (slides_ahead - cam_ahead): {offset:.2f}s")

        if abs(offset) > plausible_threshold:
            print(f"Warning: Calculated offset {offset:.2f}s is outside plausible threshold of +/-{plausible_threshold}s. Ignoring this value.")
            return None # Offset is implausible
            
        print(f"VideoSynccall determined a plausible offset: {offset:.2f}s")
        return offset # Return the single float offset

    except Exception as e:
        print(f"Error during VideoSynccall execution: {e}")
        import traceback
        traceback.print_exc()
        return None


def createpreview_from_events(slides_video_path, scene_events, video_zero_time_dt, output_image_prefix):
    """
    Generates preview PNGs from SceneChange events.
    The scene_event should have 'raw_timestamp' (datetime) and 'details.scene_name'.
    """
    # from timecode import Timecode # Not used here, direct seconds
    print(f"Generating previews for {len(scene_events)} scene events.")
    
    # Ensure the output directory for previews exists (e.g., based on output_image_prefix)
    preview_dir = os.path.dirname(output_image_prefix)
    if preview_dir and not os.path.exists(preview_dir):
        os.makedirs(preview_dir, exist_ok=True)

    for idx, event in enumerate(scene_events):
        if event['event_type'] != 'SceneChange' or not event['raw_timestamp']:
            continue

        scene_name = event['details'].get('scene_name', f"scene_{idx}")
        # Sanitize scene_name for use in filename
        safe_scene_name = "".join(c if c.isalnum() else "_" for c in scene_name)
        
        # Calculate time in seconds from video zero point
        # This assumes Slides video uses the same zero point as the main recording.
        # If slides video has its own start time, that needs to be factored in.
        # For now, assuming slides_video_path is the reference for these previews.
        
        # To get a single frame, we need the timestamp of the scene change relative to the slides video.
        # This is tricky if slides video doesn't start at video_zero_time_dt.
        # For simplicity, let's assume the event's raw_timestamp can be directly used
        # if the slides video is perfectly aligned with the main recording timeline.
        # A more robust way would be to use (event['raw_timestamp'] - slides_video_actual_start_time_dt).total_seconds()
        
        # Let's assume for now that the user will provide `secssync` correctly
        # and that the slides_video_path corresponds to the "slides" timeline.
        # The preview should be from the slides video.
        
        preview_time_sec = (event['raw_timestamp'] - video_zero_time_dt).total_seconds()
        if preview_time_sec < 0: # Scene change happened before recording start? Skip.
            print(f"Warning: SceneChange event for '{scene_name}' at {event['timestamp']} is before video zero time. Skipping preview.")
            continue

        # Generate a unique name for the preview image based on the prefix and scene name or index
        preview_filename_full = f"{output_image_prefix}_{safe_scene_name}_{idx}.png"
        lower_third_filename_full = f"{output_image_prefix}_{safe_scene_name}_{idx}_l3.png"

        if os.path.isfile(preview_filename_full):
            print(f"Preview file {preview_filename_full} already exists, skipping generation.")
            continue
        try:
            with VideoFileClip(slides_video_path) as aclip:
                 # Save frame slightly after the scene change to ensure it's loaded
                aclip.save_frame(preview_filename_full, t=preview_time_sec + 0.1)
            print(f"Created Preview PNG: {preview_filename_full} for scene '{scene_name}' at {preview_time_sec:.2f}s")
            
            # Imagemagick call for lower third (ensure ImageMagick is installed and `convert` is in PATH)
            # This command might need adjustment depending on OS and ImageMagick version
            convert_command = f'convert "{preview_filename_full}" -crop 1280x635+0+60 -trim -resize 30% "{lower_third_filename_full}"'
            call(convert_command, shell=True) # Using shell=True for simplicity, consider security implications
            print(f"Created Lower Third PNG: {lower_third_filename_full}")

        except Exception as e:
            print(f"Error creating preview for event {event}: {e}")
            # If there's an error, ensure the preview_filename is not used later or is None
            # For now, just print error and continue.
    return # Returns nothing, modifies files on disk


def quickedit_event_driven(segment_info, camera_file, slides_file, secsync, logo_bug_path_from_config, output_prefix_from_config, video_zero_time_dt):
    """
    Processes a single video segment based on event data.
    segment_info is a dictionary from generate_segments_from_events.
    """
    timestr = datetime.now().strftime("%Y-%m-%d-%H-%M-%S") # More unique timestamp
    
    title = segment_info.get('Title', f"Segment_{timestr}")
    presentation = segment_info.get('presentation', 'third') # Default presentation style
    
    # Calculate clip start and end times in seconds relative to video_zero_time_dt
    segment_start_sec = (segment_info['start_time_dt'] - video_zero_time_dt).total_seconds()
    segment_end_sec = (segment_info['end_time_dt'] - video_zero_time_dt).total_seconds()
    
    if segment_start_sec < 0: segment_start_sec = 0 # Clamp to video start
    if segment_end_sec < segment_start_sec:
        print(f"Warning: Segment '{title}' end time is before start time. Skipping.")
        return

    # Camera video times
    camera_start_sec = segment_start_sec - secsync # Apply sync offset for camera
    camera_end_sec = segment_end_sec - secsync
    
    if camera_start_sec < 0: camera_start_sec = 0

    # Slides video times - centered around the primary slide event if available
    slide_event_dt = segment_info.get('slide_event_timestamp_dt')
    initial_slide_png = segment_info.get('initial_slide_png_path', '') # Path to pre-generated PNG

    # Default slide video timing to match camera segment if no specific slide event time
    slides_start_sec = segment_start_sec
    slides_end_sec = segment_end_sec

    if slide_event_dt:
        # If a specific slide event is tied to this segment, we might want the slides
        # video to focus on that. For an "overlay" or "third", the slide might be
        # shown for the duration of the voice segment.
        # For a "title" style, it might be a still image.
        # This part needs careful thought based on desired output.
        # For now, let's assume the main segment times are for voice, and slide video matches that.
        # The `initial_slide_png` is used for "title" or "third".
        pass # Using segment_start_sec and segment_end_sec for slides video for now.
             # More advanced logic could use slide_event_dt to cut the slide video
             # more precisely around the slide change. e.g.,
             # slides_start_sec = (slide_event_dt - video_zero_time_dt).total_seconds()
             # slides_end_sec = slides_start_sec + 5 # Show slide for 5 seconds
    
    print(f"Processing segment: {title}")
    print(f"  Segment time (abs): {segment_info['start_time_dt']} to {segment_info['end_time_dt']}")
    print(f"  Video zero time: {video_zero_time_dt}")
    print(f"  Segment time (rel sec): {segment_start_sec:.2f}s to {segment_end_sec:.2f}s")
    print(f"  Camera time (rel sec): {camera_start_sec:.2f}s to {camera_end_sec:.2f}s (sync: {secsync}s)")
    print(f"  Slides video time (rel sec): {slides_start_sec:.2f}s to {slides_end_sec:.2f}s")
    if slide_event_dt:
        print(f"  Primary slide event at (abs): {slide_event_dt}")
    if initial_slide_png:
        print(f"  Using initial slide PNG: {initial_slide_png}")

    try:
        # Ensure output directory exists
        if output_prefix_from_config:
            os.makedirs(output_prefix_from_config, exist_ok=True)
            # print(f"Ensured output directory exists: {output_prefix_from_config}") # Less verbose

        # Load main clips
        # Using 'with' might be better if MoviePy objects need explicit closing.
        # For now, following existing pattern.
        camera_video_full = VideoFileClip(camera_file)
        slides_video_full = VideoFileClip(slides_file)

        camera_subclip = camera_video_full.subclip(camera_start_sec, camera_end_sec).fx(afx.volumex, 2)
        slides_subclip = slides_video_full.subclip(slides_start_sec, slides_end_sec).fx(vfx.mask_color, [255, 255, 255], thr=10, s=8).set_opacity(.7).set_pos('center').fx(afx.volumex, 0)

        # Prepare layers
        clips_to_composite = [camera_subclip]
        white_bg = ColorClip(size=camera_subclip.size, col=[255,255,255], duration=camera_subclip.duration).set_opacity(0.5)

        if presentation == "overlay":
            clips_to_composite.extend([white_bg.crossfadein(1).crossfadeout(1), slides_subclip.crossfadein(1).crossfadeout(1)])
        elif presentation == "title":
            if initial_slide_png and os.path.exists(initial_slide_png):
                slide_still_img = ImageClip(initial_slide_png).set_duration(min(7, camera_subclip.duration)) # Show for 7s or clip duration
                clips_to_composite.append(slide_still_img.crossfadein(1).crossfadeout(1))
            else:
                print(f"Warning: Slide PNG {initial_slide_png} not found for title presentation. Skipping slide.")
        elif presentation == "third":
            # Path for lower third should be derived from initial_slide_png (e.g., _l3 version)
            if initial_slide_png and os.path.exists(initial_slide_png.replace(".png", "_l3.png")):
                lower_third_png = initial_slide_png.replace(".png", "_l3.png")
                lower_third_img = (ImageClip(lower_third_png)
                                   .set_pos(lambda t: ("center", (camera_subclip.h * 0.95) - lower_third_img.h)) # Position needs access to its own height
                                   .set_duration(camera_subclip.duration * 0.45) # Show for 45% of segment
                                   .set_opacity(0.7))
                # Correcting pos lambda to access its own height (common pattern)
                # This lambda for set_pos can be tricky. If lower_third_img.h is not fixed, this is problematic.
                # Assuming lower_third_img is loaded once to get its height, then used.
                # For simplicity, let's assume its height is somewhat known or can be pre-calculated if issues arise.
                # A fixed position or a simpler lambda might be safer if dynamic sizing is complex.
                # Example fixed: .set_pos(("center", camera_subclip.h * 0.8))
                clips_to_composite.append(lower_third_img.crossfadein(1).crossfadeout(1))
            else:
                print(f"Warning: Lower third PNG (derived from {initial_slide_png}) not found. Skipping lower third.")
        
        # Add logo bug
        if logo_bug_path_from_config and os.path.exists(logo_bug_path_from_config):
            logo_clip = (ImageClip(logo_bug_path_from_config)
                         .resize(height=(camera_subclip.h * 0.1))
                         .set_pos(lambda t: (((camera_subclip.w * 0.97) - logo_clip.w), ((t / camera_subclip.duration) * (camera_subclip.h - logo_clip.h))))
                         .set_duration(camera_subclip.duration)
                         .set_opacity(0.6))
            clips_to_composite.append(logo_clip)
        else:
            print(f"Warning: Logo bug image {logo_bug_path_from_config} not found. Bug will not be added.")

        final_clip = CompositeVideoClip(clips_to_composite)
        
        # Output filename
        safe_title = "".join(c if c.isalnum() else "_" for c in title)
        output_filename = f"{safe_title}_{timestr}.mp4"
        final_output_path = os.path.join(output_prefix_from_config or ".", output_filename)
        
        print(f"Outputting to: {final_output_path}")
        final_clip.write_videofile(final_output_path,
                                   write_logfile=False,
                                   codec='libx264',
                                   audio_codec='aac',
                                   temp_audiofile=(os.path.join(output_prefix_from_config or ".", f"temp_audio_{safe_title}_{timestr}.m4a")),
                                   preset="ultrafast", # Consider medium for better quality if time allows
                                   remove_temp=True,
                                   threads=4) # Example: use multiple threads for encoding

    except Exception as e:
        print(f"Error processing segment '{title}': {e}")
        import traceback
        traceback.print_exc()
    finally:
        # MoviePy can leave files open or processes running. Explicitly close.
        if 'camera_video_full' in locals() and hasattr(camera_video_full, 'close'): camera_video_full.close()
        if 'slides_video_full' in locals() and hasattr(slides_video_full, 'close'): slides_video_full.close()
        if 'final_clip' in locals() and hasattr(final_clip, 'close'): final_clip.close()
        # May need to close other ImageClips if they hold resources.


def to_relative_seconds(event_dt, video_zero_dt):
    if not event_dt or not video_zero_dt:
        return None
    return (event_dt - video_zero_dt).total_seconds()

def generate_segments_from_events(events, video_zero_time_dt, slide_preview_base_path):
    """
    Generates video editing segments from parsed log events.
    Focuses on MicUnmute/MicMute pairs to define segments.
    """
    segments = []
    active_mics = {} # To track start time of MicUnmute for each mic

    # Sort events by raw_timestamp if not already sorted
    # Assuming events from log_parser are roughly chronological but sorting is safer
    events.sort(key=lambda e: e['raw_timestamp'] if e['raw_timestamp'] else datetime.min)

    for event in events:
        if not event['raw_timestamp']: # Skip events without a valid timestamp
            continue

        event_type = event['event_type']
        mic_name = event['details'].get('mic_name') if event_type in ['MicMute', 'MicUnmute'] else None

        if event_type == 'MicUnmute' and mic_name:
            if mic_name in active_mics:
                # This mic was unmuted again before being muted. Treat previous unmute as orphaned.
                print(f"Warning: Mic '{mic_name}' unmuted again at {event['timestamp']} before previous mute. Resetting start for this mic.")
            active_mics[mic_name] = event # Store the entire event
        
        elif event_type == 'MicMute' and mic_name:
            if mic_name in active_mics:
                start_event = active_mics.pop(mic_name) # Remove mic from active, get its start event
                
                segment_start_dt = start_event['raw_timestamp']
                segment_end_dt = event['raw_timestamp']

                if segment_end_dt <= segment_start_dt:
                    print(f"Warning: Mic '{mic_name}' muted at/before unmute time. Start: {segment_start_dt}, End: {segment_end_dt}. Skipping segment.")
                    continue

                # Find the most relevant SceneChange event within this segment
                primary_slide_event = None
                # Look for SceneChange events between segment_start_dt and segment_end_dt
                # Prefer the one closest to segment_start_dt
                relevant_scene_changes = [
                    sc_event for sc_event in events 
                    if sc_event['event_type'] == 'SceneChange' and 
                       sc_event['raw_timestamp'] and
                       segment_start_dt <= sc_event['raw_timestamp'] < segment_end_dt
                ]
                if relevant_scene_changes:
                    # Sort by time difference from segment_start_dt
                    relevant_scene_changes.sort(key=lambda sc: abs(sc['raw_timestamp'] - segment_start_dt))
                    primary_slide_event = relevant_scene_changes[0]
                
                title = f"Segment_{mic_name.replace(' ', '_')}_{segment_start_dt.strftime('%H%M%S')}"
                
                initial_png_path = None
                if primary_slide_event:
                    scene_name_for_path = "".join(c if c.isalnum() else "_" for c in primary_slide_event['details'].get('scene_name', 'unknownscene'))
                    # Find the index of this primary_slide_event among all scene changes to make filename unique like in createpreview
                    # This is a bit complex; for now, let's use a simpler naming for PNG path if possible,
                    # or assume createpreview_from_events can be called first to generate these with known names.
                    # Let's assume `slide_preview_base_path` is like `output/previews/video_date_prefix`
                    # and we append `_SceneName_idx.png` to it.
                    # This requires `createpreview_from_events` to be run first and use a predictable naming.
                    # For now, just store the scene name. The actual path construction will be tricky.
                    # Placeholder for now:
                    # initial_png_path = f"{slide_preview_base_path}_{scene_name_for_path}.png" 
                    # This needs to match what createpreview_from_events generates.

                segments.append({
                    'Title': title,
                    'Person': mic_name, # Or more descriptive name later
                    'start_time_dt': segment_start_dt,
                    'end_time_dt': segment_end_dt,
                    'slide_event_timestamp_dt': primary_slide_event['raw_timestamp'] if primary_slide_event else None,
                    'slide_scene_name': primary_slide_event['details'].get('scene_name') if primary_slide_event else None,
                    'initial_slide_png_path': initial_png_path, # To be properly determined
                    'presentation': 'third' # Default
                })
            else:
                # Mute event without a corresponding unmute (e.g., mic was muted at script start)
                print(f"Info: Mic '{mic_name}' muted at {event['timestamp']} without a prior unmute in this session.")
                
    # Handle mics that were unmuted but never muted before end of log
    for mic_name, start_event in active_mics.items():
        print(f"Warning: Mic '{mic_name}' was unmuted at {start_event['timestamp']} but never muted before end of log. Creating segment until end of log (or last event).")
        # Decide how to handle this: segment until last event time? Or discard?
        # For now, let's create a segment until the timestamp of the very last event in the log.
        if events:
            last_event_time_dt = events[-1]['raw_timestamp']
            if last_event_time_dt and last_event_time_dt > start_event['raw_timestamp']:
                segments.append({
                    'Title': f"Segment_{mic_name.replace(' ', '_')}_{start_event['raw_timestamp'].strftime('%H%M%S')}_incomplete",
                    'Person': mic_name,
                    'start_time_dt': start_event['raw_timestamp'],
                    'end_time_dt': last_event_time_dt, # End at the time of the last recorded event
                    'slide_event_timestamp_dt': None, # Cannot reliably determine slide for this
                    'slide_scene_name': None,
                    'initial_slide_png_path': None,
                    'presentation': 'third'
                })

    return segments


# Deprecating old quickedit in favor of quickedit_event_driven
# def quickedit(Scenes,Requests,Files,secssync, logo_bug_path_from_config, output_prefix_from_config):
    # ... (old implementation) ...

# Deprecating allscenesarevalid as its role is replaced by generate_segments_from_events
# def allscenesarevalid(Scenes,Requests,Files,secssync):
    # ... (old implementation) ...

def concatRequests(Scenes,Requests,Files):
    #Try to Concat the Files With the Text File Created in quickpreview function..... this is bad code.
    pass

# Use configuration for paths
obs_log_path = config.get("obs_infowriter_log", DEFAULT_CONFIG["obs_infowriter_log"])
video_search_path = config.get("video_search_path", DEFAULT_CONFIG["video_search_path"])
logo_bug_path_main = config.get("logo_bug_path", DEFAULT_CONFIG["logo_bug_path"])
output_path_prefix_main = config.get("output_path_prefix", DEFAULT_CONFIG["output_path_prefix"])

# Ensure output directory exists for general outputs
if output_path_prefix_main:
    os.makedirs(output_path_prefix_main, exist_ok=True)

# --- Main Execution Flow ---

# 1. Find Video Files (Camera and Slides)
# This logic remains similar, but ensure `Files` are correctly identified.
if not Files: # If Files list is not pre-populated
    Files = find("*"+today.strftime('%Y-%m-%d')+"*.mp4", video_search_path)
    if not Files:
        print(f"Warning: No video files found for today in {video_search_path}. Attempting last week.")
        # Scenes = findscenes(lastweek, obs_log_path) # This is for old system
        Files = find("*"+lastweek.strftime('%Y-%m-%d')+"*.mp4", video_search_path)
        if not Files:
            print(f"Error: No video files found for today or last week in {video_search_path}. Exiting.")
            sys.exit(1)
    # print("Files are in the Array Skipping find Step" if Files else "No files found.") # Python 3 print

if not Files or len(Files) < 2:
    print("Error: Not enough video files found (expected at least Camera and Slides). Please check video_search_path in config. Exiting.")
    sys.exit(1)

camera_video_file = Files[0] # Assuming first file is camera
slides_video_file = Files[1] # Assuming second file is slides
print(f"Using Camera File: {camera_video_file}")
print(f"Using Slides File: {slides_video_file}")


# 2. Parse the Consolidated Log File
# Path for parse_log_file: (assuming Sampleoutput is at repo root, and this script is in python-editor)
log_parser_input_file = "../Sampleoutput/2017-06-02_17-36-Slides.txt" # Example, make this configurable or auto-detected
if not os.path.exists(log_parser_input_file):
    print(f"Error: Consolidated log file for parser not found at {log_parser_input_file}. Exiting.")
    sys.exit(1)
    
print(f"\nParsing consolidated log file: {log_parser_input_file}")
parsed_log_events = parse_log_file(log_parser_input_file)

if not parsed_log_events:
    print("Error: No events parsed from the log file. Cannot proceed. Exiting.")
    sys.exit(1)

# 3. Determine Video Zero Time (Recording Start)
video_zero_time_dt = None
for event in parsed_log_events:
    if event['event_type'] == 'RecordingStart' and event['raw_timestamp']:
        video_zero_time_dt = event['raw_timestamp']
        break
if not video_zero_time_dt:
    print("Warning: No 'RecordingStart' event found in logs. Trying to use file creation time (less reliable) or first event time.")
    # Fallback: use the timestamp of the first event in the log if available
    for event in parsed_log_events:
        if event['raw_timestamp']:
            video_zero_time_dt = event['raw_timestamp']
            print(f"Using timestamp of first log event as video zero time: {video_zero_time_dt}")
            break
    if not video_zero_time_dt:
        print("Error: Cannot determine video zero time from logs. Exiting.")
        sys.exit(1)

print(f"Video Zero Time (Recording Start or First Event): {video_zero_time_dt}")

# 4. Generate Previews from SceneChange Events in Parsed Log
# Define a base path/prefix for preview images, e.g., in the output directory
preview_image_prefix = os.path.join(output_path_prefix_main, f"preview_{today.strftime('%Y%m%d')}")

all_scene_change_events = [e for e in parsed_log_events if e['event_type'] == 'SceneChange' and e['raw_timestamp']]
if all_scene_change_events:
    createpreview_from_events(slides_video_file, all_scene_change_events, video_zero_time_dt, preview_image_prefix)
else:
    print("No SceneChange events found in parsed log to generate previews from.")

# 5. Generate Segments from Events
# The slide_preview_base_path needs to align with how createpreview_from_events names files.
# For now, generate_segments_from_events will store scene_name, and quickedit_event_driven
# will try to form the preview path.
print("\nGenerating segments from parsed events...")
generated_segments = generate_segments_from_events(parsed_log_events, video_zero_time_dt, preview_image_prefix)

if not generated_segments:
    print("No segments were generated based on Mic activity. Exiting.")
    sys.exit(0) # Not an error, but nothing to do

# 6. Get Sync Offset (Camera to Slides)
print("\n--- Sync Offset Determination ---")
alignment_settings_for_call = config.get('alignment_settings', {}) # Use loaded or default alignment settings

# Call VideoSynccall, which now returns a single offset (float) or None
calculated_sync_offset = None # Initialize
# Toggle for enabling/disabling actual call to VideoSynccall
enable_auto_sync_call = False # Set to True to attempt automatic sync calculation

if enable_auto_sync_call:
    try:
        print("Attempting automatic sync calculation via VideoSynccall...")
        calculated_sync_offset = VideoSynccall(camera_video_file, slides_video_file, alignment_settings_for_call)
        if calculated_sync_offset is not None:
            print(f"Automatic sync calculation successful. Calculated offset: {calculated_sync_offset:.2f}s")
        else:
            print("Automatic sync calculation did not yield a plausible offset.")
    except Exception as e:
        print(f"Error during automatic VideoSynccall: {e}. Proceeding with manual input.")
        calculated_sync_offset = None # Ensure it's None if an error occurred
else:
    print("Automatic sync calculation (VideoSynccall) is currently disabled.")

# Pass the calculated_sync_offset (which can be None) to userpromptssync
secssync = userpromptssync(calculated_sync_offset)

print(f"Final Sync Offset (secssync) to be used: {secssync:.2f} seconds")
print("(Positive secsync means slides are ahead of camera; camera footage will be shifted by +secssync)")
print("(Negative secsync means camera is ahead of slides; camera footage will be shifted by +secssync)")
print("-----------------------------")


# 7. Process Segments with quickedit_event_driven
print(f"\nStarting to process {len(generated_segments)} segments...")
for segment in generated_segments:
    # Update initial_slide_png_path for the segment to match createpreview_from_events logic
    if segment['slide_scene_name']:
        safe_scene_name = "".join(c if c.isalnum() else "_" for c in segment['slide_scene_name'])
        # This needs to find the correct index if multiple scenes have the same name.
        # This is a simplification. A more robust way would be to have createpreview return a map.
        # For now, we'll try to guess the first preview matching the scene name.
        # This is still problematic as idx is not available here.
        # Let's assume for now that the `initial_slide_png_path` can be constructed if the scene name is unique enough
        # or if we simplify `createpreview_from_events` to not use idx if scene names are unique.
        # A temporary fix: try to find the first preview that matches this scene name.
        # This is not robust.
        # A better way: generate_segments_from_events should try to find the *exact* preview file
        # by knowing how createpreview_from_events names them (e.g. by passing the full scene event to make the name).
        
        # Let's refine initial_slide_png_path within generate_segments_from_events or assume it's done there.
        # For now, we'll construct a potential path, but this is a known weak point.
        # The `idx` part is missing. If `createpreview_from_events` can make unique names from scene_name + timestamp, that's better.
        # Let's assume `generate_segments_from_events` now sets `initial_slide_png_path` more accurately if possible.
        # If not, `quickedit_event_driven` will check for its existence.
        
        # Simplification: Let `generate_segments_from_events` try to create a plausible name,
        # and `quickedit_event_driven` will use it if the file exists.
        # Example: if primary_slide_event is passed to a helper in generate_segments...
        # For this iteration, the current `initial_slide_png_path` set by `generate_segments_from_events` (which is None)
        # will be passed. `quickedit_event_driven` will handle it if it's None or file not found.
        # To make it slightly better, let's try to form a path if scene_name is available:
        if segment.get('slide_scene_name'):
             # This is a simplified guess, assumes createpreview_from_events made a file like this.
             # This is NOT robust because of the missing index from preview generation.
             # A proper solution would involve `createpreview_from_events` returning a map of scene_event to filename.
             # Or `generate_segments_from_events` needs to find the matching preview based on the scene event.
             # For now, let's assume `initial_slide_png_path` might be None and quickedit handles it.
             pass


    quickedit_event_driven(
        segment_info=segment,
        camera_file=camera_video_file,
        slides_file=slides_video_file,
        secsync=secssync,
        logo_bug_path_from_config=logo_bug_path_main,
        output_prefix_from_config=output_path_prefix_main,
        video_zero_time_dt=video_zero_time_dt
    )

# --- Old Main Execution Logic (Commented out or removed) ---
# Scenes = findscenes(today, obs_log_path) # Old way of getting scenes
# ... (old calls to createpreview, allscenesarevalid, quickedit) ...

# --- Log Parser Integration (Original Position - now integrated into main flow) ---
# def process_events_from_log_parser(events_list): ...
# log_parser_input_file = "../Sampleoutput/2017-06-02_17-36-Slides.txt" 
# if os.path.exists(log_parser_input_file):
#     print(f"\nAttempting to parse consolidated log file: {log_parser_input_file}")
#     parsed_log_events = parse_log_file(log_parser_input_file) # This is now done earlier
#     process_events_from_log_parser(parsed_log_events) # This function's purpose is now for debug/display
# else:
#     print(f"\nWarning: Consolidated log file for parser not found at {log_parser_input_file}. Skipping this step.")

# Display parsed events for debugging if needed (using the existing function)
if parsed_log_events:
    process_events_from_log_parser(parsed_log_events)


# os.system("pause") # This may not be desirable in an automated script
print("Script finished.")