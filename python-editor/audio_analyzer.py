import argparse
import os
import numpy as np
import pprint # Added for standardized output

from pyAudioAnalysis.ShortTermFeatures import feature_extraction
from pyAudioAnalysis.audioBasicIO import read_audio_file, stereo_to_mono
from pyAudioAnalysis import audioSegmentation as aS

def extract_short_term_features(audio_file_path):
    """
    Extracts and prints a summary of short-term audio features from an audio file.
    """
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return

    try:
        print(f"Processing audio file for Feature Extraction: {audio_file_path}...")

        sampling_rate, signal = read_audio_file(audio_file_path)

        if not isinstance(signal, np.ndarray):
            signal = np.array(signal)

        if signal.ndim == 2: # Stereo
            print("Input signal is stereo. Converting to mono.")
            signal = stereo_to_mono(signal)
        
        if signal.ndim != 1:
            print(f"Error: Signal is not mono after potential conversion. Shape: {signal.shape}")
            return
        
        win_samples = int(sampling_rate * 0.050)
        step_samples = int(sampling_rate * 0.025)

        print(f"Using window size: {0.050}s ({win_samples} samples)")
        print(f"Using window step: {0.025}s ({step_samples} samples)")

        features, feature_names = feature_extraction(signal, sampling_rate, win_samples, step_samples)

        print(f"\n--- Feature Extraction Summary ---")
        print(f"Audio File: {os.path.basename(audio_file_path)}")
        print(f"Sampling Rate: {sampling_rate} Hz")
        print(f"Signal Length: {len(signal)} samples ({len(signal)/float(sampling_rate):.2f} seconds)")
        print(f"Signal Shape (after mono conversion if any): {signal.shape}")
        print(f"Number of short-term windows processed: {features.shape[1]}")
        print(f"Number of features extracted per window: {features.shape[0]}")
        
        print("\nFeature Names:")
        for i, name in enumerate(feature_names):
            print(f"  {i+1}. {name}")

        num_windows_to_show = min(3, features.shape[1])
        num_features_to_show = min(5, features.shape[0])
        
        print(f"\nExample Features (first {num_windows_to_show} windows, first {num_features_to_show} features):")
        for w_idx in range(num_windows_to_show):
            feature_values = [f"{features[f_idx, w_idx]:.4f}" for f_idx in range(num_features_to_show)]
            print(f"  Window {w_idx+1}: [{', '.join(feature_values)} ... ]")
        
        print("--- End of Feature Extraction Summary ---")

    except Exception as e:
        print(f"Error during Feature Extraction for {audio_file_path}: {e}")
        import traceback
        traceback.print_exc()

def perform_speaker_diarization(audio_file_path, num_speakers):
    """
    Performs speaker diarization and returns a list of standardized event dictionaries.
    """
    standardized_events = []
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return standardized_events # Return empty list

    try:
        print(f"\n--- Performing Speaker Diarization for {num_speakers} speakers on {os.path.basename(audio_file_path)} ---")
        
        mid_window_s = 2.0
        mid_step_s = 0.2
        short_window_s = 0.05
        short_step_s = 0.025
        lda_dim = 0

        speaker_labels = aS.speaker_diarization(audio_file_path, num_speakers, 
                                                mid_window=mid_window_s, mid_step=mid_step_s, 
                                                short_window=short_window_s, short_step=short_step_s, 
                                                lda_dim=lda_dim, plot_results=False)

        if speaker_labels is not None and len(speaker_labels) > 0:
            print("\n--- Processed Speaker Segments (Raw) ---") # Info before standardization
            current_speaker_label = int(speaker_labels[0])
            segment_start_time_sec = 0.0
            
            for i in range(1, len(speaker_labels)):
                if int(speaker_labels[i]) != current_speaker_label:
                    segment_end_time_sec = i * mid_step_s
                    duration_sec = segment_end_time_sec - segment_start_time_sec
                    speaker_id_str = f"Speaker_{current_speaker_label}"
                    
                    standardized_events.append({
                        'event_type': 'SpeakerSegment',
                        'start_time_sec': round(segment_start_time_sec, 3),
                        'end_time_sec': round(segment_end_time_sec, 3),
                        'duration_sec': round(duration_sec, 3),
                        'details': {'speaker_id': speaker_id_str}
                    })
                    # For verbose printing during development/testing (can be removed for cleaner output)
                    # print(f"{speaker_id_str}: From {segment_start_time_sec:.2f}s to {segment_end_time_sec:.2f}s (Duration: {duration_sec:.2f}s)")

                    current_speaker_label = int(speaker_labels[i])
                    segment_start_time_sec = segment_end_time_sec
            
            final_segment_end_time_sec = len(speaker_labels) * mid_step_s
            final_duration_sec = final_segment_end_time_sec - segment_start_time_sec
            final_speaker_id_str = f"Speaker_{current_speaker_label}"

            standardized_events.append({
                'event_type': 'SpeakerSegment',
                'start_time_sec': round(segment_start_time_sec, 3),
                'end_time_sec': round(final_segment_end_time_sec, 3),
                'duration_sec': round(final_duration_sec, 3),
                'details': {'speaker_id': final_speaker_id_str}
            })
            # print(f"{final_speaker_id_str}: From {segment_start_time_sec:.2f}s to {final_segment_end_time_sec:.2f}s (Duration: {final_duration_sec:.2f}s)")
            # print(f"(Note: Diarization segments are based on mid-term windows of {mid_step_s:.2f}s step size.)")
        else:
            print("Speaker diarization did not return any labels or failed.")
        
        print("--- End of Speaker Diarization ---")

    except Exception as e:
        print(f"Error during speaker diarization for {audio_file_path}: {e}")
        import traceback
        traceback.print_exc()
    return standardized_events

def perform_sound_event_detection(audio_file_path):
    """
    Performs sound event detection (example: silence removal) and returns a list of standardized event dictionaries.
    """
    standardized_events = []
    if not os.path.exists(audio_file_path):
        print(f"Error: Audio file not found at {audio_file_path}")
        return standardized_events # Return empty list

    try:
        print(f"\n--- Performing Sound Event Detection (Silence Removal example) on {os.path.basename(audio_file_path)} ---")
        
        sampling_rate, signal = read_audio_file(audio_file_path)

        if not isinstance(signal, np.ndarray):
            signal = np.array(signal)

        if signal.ndim > 1: 
            print("Input signal is stereo. Converting to mono for sound event detection.")
            signal = stereo_to_mono(signal)
        
        if signal.ndim != 1:
            print(f"Error: Signal is not mono after potential conversion for sound event detection. Shape: {signal.shape}")
            return standardized_events

        st_win_secs = 0.050
        st_step_secs = 0.025
        smooth_window_secs = 0.5
        weight_param = 0.3

        print(f"Parameters for silence_removal: st_win={st_win_secs}s, st_step={st_step_secs}s, smooth_window={smooth_window_secs}s, weight={weight_param}")
        
        segments = aS.silence_removal(signal, sampling_rate, st_win_secs, st_step_secs, smooth_window_secs, weight_param, plot_results=False)
        
        # print("\nDetected sound segments (i.e., non-silence regions):") # Old print
        if segments.size == 0 or segments.shape[0] == 0:
            print("No distinct sound segments detected (file might be all silence or all sound based on current parameters).")
        else:
            for s_start, s_end in segments:
                duration = s_end - s_start
                standardized_events.append({
                    'event_type': 'SoundSegment',
                    'start_time_sec': round(s_start, 3),
                    'end_time_sec': round(s_end, 3),
                    'duration_sec': round(duration, 3),
                    'details': {'segment_type': 'sound'}
                })
                # print(f"  Sound detected: From {s_start:.2f}s to {s_end:.2f}s (Duration: {duration:.2f}s)") # Old print
        
        print("\nNote: This example uses silence removal. Detecting specific events like 'piano' or 'singing' accurately typically requires custom-trained models and more advanced techniques.")
        print("pyAudioAnalysis provides tools for training such classifiers if you have labeled data.")
        print("--- End of Sound Event Detection ---")

    except Exception as e:
        print(f"Error during sound event detection for {audio_file_path}: {e}")
        import traceback
        traceback.print_exc()
    return standardized_events

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract audio features, perform speaker diarization, and/or detect sound events."
    )
    parser.add_argument(
        "audio_file", 
        help="Path to the audio file (e.g., WAV, MP3)."
    )
    parser.add_argument(
        "--features", 
        action="store_true", 
        help="Extract and display short-term audio features."
    )
    parser.add_argument(
        "--diarize", 
        action="store_true", 
        help="Perform speaker diarization."
    )
    parser.add_argument(
        "--sound_events",
        action="store_true",
        help="Perform basic sound event detection (e.g., silence removal)."
    )
    parser.add_argument(
        "--num_speakers", 
        type=int, 
        default=0,
        help="Number of speakers for diarization. Required if --diarize is used and model doesn't auto-detect."
    )
    
    args = parser.parse_args()

    if not args.features and not args.diarize and not args.sound_events:
        print("No action specified. Use --features, --diarize, or --sound_events.")
        parser.print_help()
    
    if args.features:
        extract_short_term_features(args.audio_file)

    if args.diarize:
        if args.num_speakers <= 0:
            print("Error: --num_speakers must be a positive integer for diarization.")
            print("Please specify the number of speakers using --num_speakers (e.g., --num_speakers 2).")
        else:
            diarization_events = perform_speaker_diarization(args.audio_file, args.num_speakers)
            if diarization_events: # Check if list is not empty
                print("\n--- Standardized Speaker Diarization Output ---")
                pprint.pprint(diarization_events)
    
    if args.sound_events:
        sound_events = perform_sound_event_detection(args.audio_file)
        if sound_events: # Check if list is not empty
            print("\n--- Standardized Sound Event Detection Output ---")
            pprint.pprint(sound_events)
```
