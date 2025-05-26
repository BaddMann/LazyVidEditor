import scipy.io.wavfile
import numpy as np
from subprocess import call
import math


# Extract audio from video file, save as wav auido file
# INPUT: Video file
# OUTPUT: Does not return any values, but saves audio as wav file
def extract_audio(dir, video_file):
    track_name = video_file.split(".")
    audio_output = track_name[0] + "WAV.wav"  # !! CHECK TO SEE IF FILE IS IN UPLOADS DIRECTORY
    output = dir + audio_output
    call(["ffmpeg", "-loglevel", "panic", "-hide_banner", "-y", "-i", dir+video_file, "-vn", "-ac", "1", "-f", "wav", output])
    return output


# Read file
# INPUT: Audio file
# OUTPUT: Sets sample rate of wav file, Returns data read from wav file (numpy array of integers)
def read_audio(audio_file):
    rate, data = scipy.io.wavfile.read(audio_file)  # Return the sample rate (in samples/sec) and data from a WAV file
    return data, rate


def make_horiz_bins(data, fft_bin_size, overlap, box_height):
    horiz_bins = {}
    # process first sample and set matrix height
    sample_data = data[0:fft_bin_size]  # get data for first sample
    if (len(sample_data) == fft_bin_size):  # if there are enough audio points left to create a full fft bin
        intensities = fourier(sample_data)  # intensities is list of fft results
        for i in range(len(intensities)):
            box_y = i/box_height
            if horiz_bins.has_key(box_y):
                horiz_bins[box_y].append((intensities[i], 0, i))  # (intensity, x, y)
            else:
                horiz_bins[box_y] = [(intensities[i], 0, i)]
    # process remainder of samples
    x_coord_counter = 1  # starting at second sample, with x index 1
    for j in range(int(fft_bin_size - overlap), len(data), int(fft_bin_size-overlap)):
        sample_data = data[j:j + fft_bin_size]
        if (len(sample_data) == fft_bin_size):
            intensities = fourier(sample_data)
            for k in range(len(intensities)):
                box_y = k/box_height
                if horiz_bins.has_key(box_y):
                    horiz_bins[box_y].append((intensities[k], x_coord_counter, k))  # (intensity, x, y)
                else:
                    horiz_bins[box_y] = [(intensities[k], x_coord_counter, k)]
        x_coord_counter += 1

    return horiz_bins


# Compute the one-dimensional discrete Fourier Transform
# INPUT: list with length of number of samples per second
# OUTPUT: list of real values len of num samples per second
def fourier(sample):  #, overlap):
    mag = []
    fft_data = np.fft.fft(sample)  # Returns real and complex value pairs
    for i in range(len(fft_data)/2):
        r = fft_data[i].real**2
        j = fft_data[i].imag**2
        mag.append(round(math.sqrt(r+j),2))

    return mag


def make_vert_bins(horiz_bins, box_width):
    boxes = {}
    for key in horiz_bins.keys():
        for i in range(len(horiz_bins[key])):
            box_x = horiz_bins[key][i][1] / box_width
            if boxes.has_key((box_x,key)):
                boxes[(box_x,key)].append((horiz_bins[key][i]))
            else:
                boxes[(box_x,key)] = [(horiz_bins[key][i])]

    return boxes


def find_bin_max(boxes, maxes_per_box):
    freqs_dict = {}
    for key in boxes.keys():
        max_intensities = [(1,2,3)]
        for i in range(len(boxes[key])):
            if boxes[key][i][0] > min(max_intensities)[0]:
                if len(max_intensities) < maxes_per_box:  # add if < number of points per box
                    max_intensities.append(boxes[key][i])
                else:  # else add new number and remove min
                    max_intensities.append(boxes[key][i])
                    max_intensities.remove(min(max_intensities))
        for j in range(len(max_intensities)):
            if freqs_dict.has_key(max_intensities[j][2]):
                freqs_dict[max_intensities[j][2]].append(max_intensities[j][1])
            else:
                freqs_dict[max_intensities[j][2]] = [max_intensities[j][1]]

    return freqs_dict


def find_freq_pairs(freqs_dict_orig, freqs_dict_sample):
    time_pairs = []
    for key in freqs_dict_sample.keys():  # iterate through freqs in sample
        if freqs_dict_orig.has_key(key):  # if same sample occurs in base
            for i in range(len(freqs_dict_sample[key])):  # determine time offset
                for j in range(len(freqs_dict_orig[key])):
                    time_pairs.append((freqs_dict_sample[key][i], freqs_dict_orig[key][j]))

    return time_pairs


def find_delay(time_pairs):
    t_diffs = {}
    for i in range(len(time_pairs)):
        delta_t = time_pairs[i][0] - time_pairs[i][1]
        if delta_t in t_diffs: # Python 3 style check
            t_diffs[delta_t] += 1
        else:
            t_diffs[delta_t] = 1
    
    print(f"Time differences counts: {t_diffs}") # Added diagnostic print

    if not t_diffs:
        print("Warning: Time differences dictionary (t_diffs) is empty. Cannot determine delay.")
        # Depending on desired behavior, might return a specific value or raise error
        # For now, this will cause an error on the next line if t_diffs is empty.
        # Let's handle it by returning a default or raising.
        # Raising an error might be better to signal failure clearly.
        # However, to match original behavior of possibly failing on sorted(),
        # we'll let it proceed if not empty, or handle if empty.
        # The original code would fail at t_diffs_sorted[-1][0] if t_diffs was empty.
        # Let's make it explicit:
        if not t_diffs:
            print("Error: No time differences to sort, cannot find delay.")
            # Or return a specific indicator e.g. None, and let caller handle
            # For now, let's assume the expectation is it might raise an error if it can't find a delay.
            # The original code would have raised an IndexError on an empty t_diffs_sorted.
            # To prevent crash and align with returning (0,0) in align() for no pairs:
            return 0 # Return 0 samples delay if no diffs found.

    t_diffs_sorted = sorted(t_diffs.items(), key=lambda x: x[1])
    print(f"Sorted time differences: {t_diffs_sorted}") # Updated existing print to Py3 and f-string
    time_delay = t_diffs_sorted[-1][0]

    return time_delay


# Find time delay between two video files
def align(video1, video2, dir, fft_bin_size=1024, overlap=0, box_height=512, box_width=43, samples_per_box=7, duration1_secs=120, duration2_secs=60):
    print("--- Starting Alignment ---")
    print(f"Video 1: {video1}, Video 2: {video2}, Dir: {dir}")
    print(f"Parameters: fft_bin_size={fft_bin_size}, overlap={overlap}, box_height={box_height}, box_width={box_width}, samples_per_box={samples_per_box}")
    print(f"Audio Durations: video1_secs={duration1_secs}, video2_secs={duration2_secs}")

    # Process first file
    wavfile1 = extract_audio(dir, video1)
    raw_audio1, rate1 = read_audio(wavfile1) # Use rate1 specific to this audio file
    num_samples1 = int(rate1 * duration1_secs)
    # Make sure we don't try to slice beyond the length of the audio
    actual_samples1 = min(num_samples1, len(raw_audio1))
    bins_dict1 = make_horiz_bins(raw_audio1[:actual_samples1], fft_bin_size, overlap, box_height) #bins, overlap, box height
    boxes1 = make_vert_bins(bins_dict1, box_width)  # box width
    ft_dict1 = find_bin_max(boxes1, samples_per_box)  # samples per box

    # Process second file
    wavfile2 = extract_audio(dir, video2)
    raw_audio2, rate2 = read_audio(wavfile2) # Use rate2 specific to this audio file
    # It's assumed rate1 and rate2 will be similar for alignment purposes,
    # but using the specific rate for sample calculation is more robust.
    # The `samples_per_sec` calculation later uses `rate` which might be ambiguous if they differ.
    # For now, let's assume the first `rate` (rate1) is the reference for `samples_per_sec` or they are the same.
    # If rates can differ significantly, the `samples_per_sec` logic might need adjustment.
    num_samples2 = int(rate2 * duration2_secs)
    actual_samples2 = min(num_samples2, len(raw_audio2))
    bins_dict2 = make_horiz_bins(raw_audio2[:actual_samples2], fft_bin_size, overlap, box_height)
    boxes2 = make_vert_bins(bins_dict2, box_width)
    ft_dict2 = find_bin_max(boxes2, samples_per_box)

    # Determine time delay
    pairs = find_freq_pairs(ft_dict1, ft_dict2)
    print(f"Found {len(pairs)} matching frequency time pairs.") # Added diagnostic print

    if not pairs: # Handle case with no common frequency pairs
        # Message updated to be more specific to this check's outcome
        print("Warning: No matching frequency time pairs found between the audio files. Cannot determine delay.")
        print("--- Alignment Finished (No Pairs Found) ---")
        return (0, 0) # Or raise an exception, or return None
        
    delay = find_delay(pairs)
    # Use rate1 as the reference for samples_per_sec, or average if they differ, or enforce same rate.
    # Assuming rate1 is the primary reference here.
    samples_per_sec = float(rate1) / float(fft_bin_size) 
    
    if samples_per_sec == 0: # Avoid division by zero if rate1 or fft_bin_size is zero
        print("Error: samples_per_sec is zero, cannot calculate delay in seconds. Check audio rate and fft_bin_size.")
        seconds = 0 # Or handle as an error case
    else:
        seconds = round(float(delay) / float(samples_per_sec), 4)

    print(f"Calculated delay: {delay} samples, which is {seconds} seconds.") # Added diagnostic print
    print("--- Alignment Finished ---")

    if seconds > 0:
        return (seconds, 0)
    else:
        return (0, abs(seconds))



# ======= TEST FILES ==============
# audio1 = "regina6POgShQ-lC4.mp4"
# # audio2 = "reginaJo2cUWpILMgWAV.wav"
# audio1 = "Settle2kFaZIKtcn6s.mp4"
# audio2 = "Settle2d_tj-9_dGog.mp4"
# audio1 = "DanielZ5PPlk53IMY.mp4"
# audio2 = "Daniel08ycq2T_ab4.mp4"
# directory = "./uploads/"
# t = align(audio1, audio2, directory)
# print t


##### Works Very well!
##### C:\Users\glencroftplay\Documents\GitHub\pyAudioAnalysis>python audioAnalysis.py silenceRemoval -i C:\Users\glencroftplay\test.wav --smoothing 3.0 --weight 0.05


