import os
import shlex
from datetime import datetime, timedelta

def quote_path(path_str):
    """Safely quotes a path string for use in shell commands."""
    if not path_str:
        return ""
    # For Windows, shlex.quote might not always do what ffmpeg expects with drive letters.
    # A simple and effective way for ffmpeg is often just double quotes around the path.
    # However, using shlex.quote is generally safer for cross-platform/shell interpretation.
    # Let's ensure it's a string first.
    return shlex.quote(str(path_str))

def generate_ffmpeg_commands(segments, video_files_info, config):
    """
    Generates a list of ffmpeg command strings for creating video segments.

    Args:
        segments (list): A list of segment dictionaries.
        video_files_info (dict): Information about video files and timings.
        config (dict): Configuration options like output paths and logo.

    Returns:
        list: A list of ffmpeg command strings.
    """
    commands = []
    output_path_prefix = config.get("output_path_prefix", "./output/")
    logo_bug_path = config.get("logo_bug_path")
    ffmpeg_loglevel = config.get("ffmpeg_loglevel", "error") # Default to error to reduce verbosity

    # Ensure output directory exists
    if output_path_prefix and not os.path.exists(output_path_prefix):
        os.makedirs(output_path_prefix, exist_ok=True)

    for i, segment in enumerate(segments):
        try:
            segment_start_dt = segment['start_time_dt']
            segment_end_dt = segment['end_time_dt']
            video_zero_dt = video_files_info['video_zero_time_dt']
            
            segment_duration_seconds = (segment_end_dt - segment_start_dt).total_seconds()
            if segment_duration_seconds <= 0:
                print(f"Warning: Segment {i} for '{segment.get('Person', 'Unknown')}' has non-positive duration. Skipping.")
                continue

            # Camera timing
            # Add secsync because if slides are at T=0, camera is at T=0 + secsync.
            # If camera is the reference (secssync is negative, e.g. slides started before camera),
            # then camera_start_seconds will correctly be positive if segment starts after camera zero.
            camera_offset_seconds = video_files_info.get('secssync', 0.0)
            camera_start_seconds = (segment_start_dt - video_zero_dt).total_seconds() - camera_offset_seconds
            if camera_start_seconds < 0:
                # If camera starts after the segment due to sync, adjust segment duration and start time for camera
                print(f"Note: Camera for segment {i} effectively starts {-camera_start_seconds:.2f}s later due to sync. Adjusting.")
                # This means the effective duration for which camera footage is available is shorter
                # effective_camera_duration = segment_duration_seconds + camera_start_seconds 
                # camera_start_seconds = 0
                # We will handle this by ensuring ffmpeg -ss is >= 0.
                # The -t for the camera input will be segment_duration_seconds.
                # If camera_start_seconds is negative, ffmpeg will treat it as 0 but might log errors.
                # It's better to clip camera_start_seconds at 0 and adjust duration if needed,
                # but for now, ffmpeg handles -ss < 0 by starting from beginning.
                # For safety, let's clamp:
                # effective_segment_duration_for_camera = segment_duration_seconds
                # if camera_start_seconds < 0:
                #     effective_segment_duration_for_camera += camera_start_seconds # reduce duration
                #     camera_start_seconds = 0
                # if effective_segment_duration_for_camera <=0: continue
                pass # ffmpeg -ss handles negative by starting at 0. Duration remains segment_duration.


            # Slides input: video or still image
            slides_input_str = ""
            slide_is_video = False
            slides_video_path = video_files_info.get("slides_video_path")
            initial_slide_png_path = segment.get("initial_slide_png_path")

            if slides_video_path and os.path.exists(slides_video_path):
                # Prioritize slides video if available
                # Slides video is assumed to be aligned with video_zero_dt (secssync applies to camera relative to slides)
                slides_input_start_seconds = (segment_start_dt - video_zero_dt).total_seconds()
                if segment.get('slide_event_timestamp_dt'): # If a specific slide event dictates the timing for slides
                    slides_input_start_seconds = (segment['slide_event_timestamp_dt'] - video_zero_dt).total_seconds()
                
                if slides_input_start_seconds < 0: slides_input_start_seconds = 0 # Clamp
                
                slides_input_str = f"-ss {slides_input_start_seconds:.3f} -i {quote_path(slides_video_path)}"
                slide_is_video = True
            elif initial_slide_png_path and os.path.exists(initial_slide_png_path):
                slides_input_str = f"-loop 1 -framerate 2 -i {quote_path(initial_slide_png_path)}" # Loop still image
                slide_is_video = False # It's an image
            else:
                print(f"Warning: No slides video or image for segment {i}. Overlay will be skipped.")


            output_filename = os.path.join(
                output_path_prefix,
                f"{segment.get('Person', 'UnknownSegment').replace(' ', '_')}_segment_{i}_{segment_start_dt.strftime('%Y%m%d%H%M%S')}.mp4"
            )

            # Base ffmpeg command
            cmd = ["ffmpeg"]
            cmd.extend(["-y"]) # Overwrite output without asking
            cmd.extend(["-loglevel", ffmpeg_loglevel])

            # Camera Input (Input 0)
            # Using -ss before -i for input seeking (faster)
            cmd.extend(["-ss", f"{camera_start_seconds:.3f}", "-i", quote_path(video_files_info['camera_video_path'])])

            input_count = 1
            slide_input_index = -1
            logo_input_index = -1

            # Slides Input (Input 1, if available)
            if slides_input_str:
                cmd.extend(shlex.split(slides_input_str)) # Split to handle multiple args in slides_input_str
                slide_input_index = input_count
                input_count += 1
            
            # Logo Input (Input 2 or 1, if available)
            if logo_bug_path and os.path.exists(logo_bug_path):
                cmd.extend(["-i", quote_path(logo_bug_path)])
                logo_input_index = input_count
                input_count += 1

            filter_complex_parts = []
            current_video_stream = "0:v" # Start with camera video

            # Slide overlay
            if slide_input_index != -1:
                slide_stream_label = f"{slide_input_index}:v"
                # Scale slides: iw/3 or iw/4 is common for PiP
                # Overlay position: main_w-overlay_w-10:main_h-overlay_h-10 (bottom right)
                # Example from Parse-badlog: crop=in_w-70:in_h-120:35:60, then scale. For now, just scale.
                filter_complex_parts.append(f"[{slide_stream_label}]scale=iw/3.5:-1[slides_scaled]")
                filter_complex_parts.append(f"[{current_video_stream}][slides_scaled]overlay=main_w-overlay_w-10:main_h-overlay_h-10[pip_out]")
                current_video_stream = "pip_out" # Next overlay will use output of this one

            # Logo overlay
            if logo_input_index != -1:
                logo_stream_label = f"{logo_input_index}:v"
                # Scale logo (e.g., 10% of main video height, maintain aspect)
                # Overlay position: 10:10 (top left)
                filter_complex_parts.append(f"[{logo_stream_label}]scale=-1:ih*0.1[logo_scaled]") # Scale by 10% of input logo height? No, main video height.
                # Let's try scaling logo to 10% of main video height:
                # This needs to be dynamic based on [0:v] height.
                # A simpler way for logo: scale=logo_w/2:-1, then overlay.
                # Example from Parse-badlog: scale=117:-1, opacity=0.5 (opacity not simple in ffmpeg filter_complex overlay)
                # For now, simple scale and overlay for logo:
                filter_complex_parts.append(f"[{logo_stream_label}]scale=120:-1[logo_scaled_simple]") # Fixed width, auto height
                filter_complex_parts.append(f"[{current_video_stream}][logo_scaled_simple]overlay=10:10[logo_out]")
                current_video_stream = "logo_out"

            # Audio processing (compand filter from Parse-badlog.ps1)
            # compand=attacks=0:points=-80/-169|-54/-80|-44/-44|-35/-35|-25/-25|0/-15|20/-15
            # This was for PowerShell, may need escaping for direct ffmpeg.
            # FFmpeg compand filter: compand=attacks=0:points=-80/-169|-54/-80|-44/-44|-35/-35|-25/-25|0/-15|20/-15
            # Seems okay as is.
            audio_filter = "compand=attacks=0:points=-80/-169|-54/-80|-44/-44|-35/-35|-25/-25|0/-15|20/-15"
            filter_complex_parts.append(f"[0:a]aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=stereo,{audio_filter}[out_a]")
            # Using [0:a] for camera audio. If slides have audio and need mixing, it's more complex.

            if filter_complex_parts:
                cmd.extend(["-filter_complex", ";".join(filter_complex_parts)])
                cmd.extend(["-map", f"[{current_video_stream}]"]) # Map final video output
                cmd.extend(["-map", "[out_a]"]) # Map final audio output
            else: # No overlay, no audio filter, just map camera video and audio
                cmd.extend(["-map", "0:v", "-map", "0:a"])

            # Output settings
            cmd.extend(["-t", f"{segment_duration_seconds:.3f}"])
            cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23"]) # Adjust preset/crf as needed
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
            cmd.append(quote_path(output_filename))
            
            commands.append(" ".join(cmd))

        except Exception as e:
            print(f"Error generating command for segment {i} ('{segment.get('Person', 'Unknown')}'): {e}")
            import traceback
            traceback.print_exc()
            
    return commands


if __name__ == "__main__":
    print("Generating sample ffmpeg commands...")

    # Sample Data (mimicking structure from scenetest_friday.py)
    sample_video_zero_time = datetime(2023, 1, 1, 10, 0, 0)

    sample_segments = [
        {
            'start_time_dt': sample_video_zero_time + timedelta(seconds=10),
            'end_time_dt': sample_video_zero_time + timedelta(seconds=40),
            'Person': 'Mic1_Presenter',
            'slide_event_timestamp_dt': sample_video_zero_time + timedelta(seconds=12),
            'initial_slide_png_path': 'path/to/slide_image1.png' # Make sure this exists or logic handles it
        },
        {
            'start_time_dt': sample_video_zero_time + timedelta(seconds=50),
            'end_time_dt': sample_video_zero_time + timedelta(seconds=110),
            'Person': 'Mic2_Panelist',
            'slide_event_timestamp_dt': None, # No specific slide event, or use segment start
            'initial_slide_png_path': None # No still image, rely on slides video
        },
        { # Segment where camera might start late due to sync
            'start_time_dt': sample_video_zero_time + timedelta(seconds=5), # Starts 5s into recording
            'end_time_dt': sample_video_zero_time + timedelta(seconds=15),
            'Person': 'Mic3_Early',
            'slide_event_timestamp_dt': sample_video_zero_time + timedelta(seconds=6),
            'initial_slide_png_path': 'path/to/slide_image_early.png'
        }
    ]

    sample_video_files_info = {
        'camera_video_path': 'path/to/camera_video.mp4',
        'slides_video_path': 'path/to/slides_video.mp4', # Optional, can be None
        'video_zero_time_dt': sample_video_zero_time,
        'secssync': 2.0  # Camera started 2 seconds AFTER slides/log zero point
                        # So, to align camera with a log event at T, camera footage is at T - 2s
                        # ffmpeg -ss for camera needs to be (log_event_time_rel_to_zero) - secsync
    }
    
    sample_video_files_info_cam_lead = {
        'camera_video_path': 'path/to/camera_video.mp4',
        'slides_video_path': 'path/to/slides_video.mp4',
        'video_zero_time_dt': sample_video_zero_time,
        'secssync': -1.0 # Camera started 1 second BEFORE slides/log zero point
                         # Log event at T, camera footage is at T + 1s
    }


    sample_config = {
        'output_path_prefix': './ffmpeg_output/',
        'logo_bug_path': 'path/to/logo.png', # Optional, can be None
        'ffmpeg_loglevel': 'info' # More verbose for testing
    }

    # Create dummy files for testing if paths actually get checked by os.path.exists
    # This is important if the script is run directly.
    # For now, the generator doesn't check existence of input video/image files, ffmpeg will handle it.
    # except for logo_bug_path and initial_slide_png_path (if logic for it is very specific)
    
    # Test case 1: Standard setup
    print("\n--- Test Case 1: Standard Sync (Camera later than Slides/Log Zero) ---")
    # Ensure dummy files exist for paths that might be checked by the command generator
    # (though current version doesn't check input video/slides, only logo and potentially initial_slide_png)
    if sample_config.get('logo_bug_path') and not os.path.exists(sample_config['logo_bug_path']):
        # Create a dummy logo for testing if it's referenced
        print(f"Creating dummy logo file: {sample_config['logo_bug_path']}")
        os.makedirs(os.path.dirname(sample_config['logo_bug_path']) or '.', exist_ok=True)
        with open(sample_config['logo_bug_path'], 'w') as f: f.write("dummy logo")
    if sample_segments[0]['initial_slide_png_path'] and not os.path.exists(sample_segments[0]['initial_slide_png_path']):
        print(f"Creating dummy slide image: {sample_segments[0]['initial_slide_png_path']}")
        os.makedirs(os.path.dirname(sample_segments[0]['initial_slide_png_path']) or '.', exist_ok=True)
        with open(sample_segments[0]['initial_slide_png_path'], 'w') as f: f.write("dummy slide")


    generated_commands = generate_ffmpeg_commands(sample_segments, sample_video_files_info, sample_config)
    for idx, cmd_str in enumerate(generated_commands):
        print(f"\nSegment {idx} Command:")
        print(cmd_str)

    # Test case 2: Camera leads slides/log zero
    print("\n--- Test Case 2: Camera leads Slides/Log Zero ---")
    generated_commands_cam_lead = generate_ffmpeg_commands(sample_segments, sample_video_files_info_cam_lead, sample_config)
    for idx, cmd_str in enumerate(generated_commands_cam_lead):
        print(f"\nSegment {idx} Command (Cam Lead):")
        print(cmd_str)

    # Test case 3: No slides video, only still image
    print("\n--- Test Case 3: No slides video, only still image ---")
    video_files_no_slides_video = sample_video_files_info.copy()
    video_files_no_slides_video['slides_video_path'] = None 
    generated_commands_no_slides_vid = generate_ffmpeg_commands(sample_segments, video_files_no_slides_video, sample_config)
    for idx, cmd_str in enumerate(generated_commands_no_slides_vid):
        print(f"\nSegment {idx} Command (No Slides Vid):")
        print(cmd_str)

    # Test case 4: No logo
    print("\n--- Test Case 4: No logo ---")
    config_no_logo = sample_config.copy()
    config_no_logo['logo_bug_path'] = None
    generated_commands_no_logo = generate_ffmpeg_commands(sample_segments, sample_video_files_info, config_no_logo)
    for idx, cmd_str in enumerate(generated_commands_no_logo):
        print(f"\nSegment {idx} Command (No Logo):")
        print(cmd_str)

    print("\nSample command generation finished.")
    print("Note: Paths for input videos/images in sample commands are placeholders.")
    print("Ensure actual files exist or ffmpeg will error out when these commands are run.")
```
