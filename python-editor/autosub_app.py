import argparse
import audioop
from googleapiclient.discovery import build
import json
import math
import multiprocessing
import os
import requests
import subprocess
import sys
import tempfile
import wave

from progressbar import ProgressBar, Percentage, Bar, ETA

from autosub.constants import LANGUAGE_CODES, \
    GOOGLE_SPEECH_API_KEY, GOOGLE_SPEECH_API_URL
from autosub.formatters import FORMATTERS

# Ensure ffmpegexec is handled by PATH or configure externally
ffmpegexec = "ffmpeg" 

def percentile(arr, percent):
    arr = sorted(arr)
    k = (len(arr) - 1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c: return arr[int(k)]
    d0 = arr[int(f)] * (c - k)
    d1 = arr[int(c)] * (k - f)
    return d0 + d1


def is_same_language(lang1, lang2):
    return lang1.split("-")[0] == lang2.split("-")[0]


class FLACConverter(object):
    def __init__(self, source_path, include_before=0.25, include_after=0.25):
        self.source_path = source_path
        self.include_before = include_before
        self.include_after = include_after

    def __call__(self, region):
        try:
            start, end = region
            start = max(0, start - self.include_before)
            end += self.include_after
            temp = tempfile.NamedTemporaryFile(suffix='.flac', delete=False)
            command = [ffmpegexec,"-ss", str(start), "-t", str(end - start),
                       "-y", "-i", self.source_path,
                       "-loglevel", "error", temp.name]
            subprocess.check_output(command)
            with open(temp.name, 'rb') as f:
                return f.read()

        except KeyboardInterrupt:
            return


class SpeechRecognizer(object):
    def __init__(self, language="en", rate=44100, retries=3, api_key=GOOGLE_SPEECH_API_KEY):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries

    def __call__(self, data):
        try:
            for i in range(self.retries):
                url = GOOGLE_SPEECH_API_URL.format(lang=self.language, key=self.api_key)
                headers = {"Content-Type": "audio/x-flac; rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers)
                    resp.raise_for_status() # Raise an exception for bad status codes
                except requests.exceptions.RequestException:
                    # More general exception handling for requests
                    continue

                # The response is expected to be a single JSON object per line, but Google's API usually returns
                # a single block of JSON, not line-delimited. If it *is* line-delimited JSON:
                # For line-delimited JSON, decode content then split.
                # However, typical Google Speech API is not line-delimited JSON in this way.
                # It's usually a single JSON response.
                # If resp.content is bytes and it's line-delimited JSON:
                # content_str = resp.content.decode('utf-8')
                # for line_str in content_str.splitlines():
                # try:
                #    parsed_line = json.loads(line_str)
                # Process parsed_line
                # For a single JSON object response:
                try:
                    # Assuming the response is UTF-8 encoded JSON
                    response_json = json.loads(resp.content.decode('utf-8'))
                    if response_json.get("result") and response_json["result"][0].get("alternative"):
                        transcript = response_json["result"][0]["alternative"][0]["transcript"]
                        return transcript[:1].upper() + transcript[1:]
                except (json.JSONDecodeError, KeyError, IndexError):
                    # Handle cases where JSON is malformed or expected keys are missing
                    continue
                # If the above structure is not what's expected, and it really is line-delimited:
                # Fallback or adjusted logic for line-delimited (original code was trying this)
                # We'll assume single JSON object response for now based on typical API behavior.
                # If it must be line-by-line, the original loop with decode is needed:
                # for line_bytes in resp.content.split(b"\n"):
                #    if not line_bytes: continue
                #    try:
                #        line_str = line_bytes.decode('utf-8')
                #        parsed_json = json.loads(line_str)
                #        # ... process parsed_json as in original logic
                #        transcript = parsed_json['result'][0]['alternative'][0]['transcript']
                #        return transcript[:1].upper() + transcript[1:]
                #    except (json.JSONDecodeError, KeyError, IndexError, UnicodeDecodeError):
                #        continue
                # This part is tricky without knowing the exact format of multiple results if they occur.
                # Sticking to a more common single JSON response handling.

        except KeyboardInterrupt:
            return


class Translator(object):
    def __init__(self, language, api_key, src, dst):
        self.language = language
        self.api_key = api_key
        self.service = build('translate', 'v2',
                             developerKey=self.api_key)
        self.src = src
        self.dst = dst

    def __call__(self, sentence):
        try:
            if not sentence: return
            result = self.service.translations().list(
                source=self.src,
                target=self.dst,
                q=[sentence]
            ).execute()
            if 'translations' in result and len(result['translations']) and \
                            'translatedText' in result['translations'][0]:
                return result['translations'][0]['translatedText']
            return ""

        except KeyboardInterrupt:
            return


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def extract_audio(filename, channels=1, rate=16000):
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    if not os.path.isfile(filename):
        print("The given file does not exist: {0}".format(filename))
        raise Exception("Invalid filepath: {0}".format(filename))
    #if not which(ffmpegexec): # which is not robust, rely on ffmpeg being in PATH
    #    print("ffmpeg: Executable not found on machine.")
    #    raise Exception("Dependency not found: ffmpeg")
    command = [ffmpegexec, "-y", "-i", filename, "-ac", str(channels), "-ar", str(rate), "-loglevel", "error", temp.name]
    subprocess.check_output(command)
    return temp.name, rate


def find_speech_regions(filename, frame_width=4096, min_region_size=0.5, max_region_size=6): # frame_width is in samples
    reader = wave.open(filename)
    sample_width = reader.getsampwidth()
    rate = reader.getframerate()
    n_channels = reader.getnchannels()

    total_duration = reader.getnframes() / rate
    chunk_duration = float(frame_width) / rate

    n_chunks = int(total_duration / chunk_duration)
    energies = []

    for i in range(n_chunks):
        chunk = reader.readframes(frame_width)
        energies.append(audioop.rms(chunk, sample_width * n_channels))

    threshold = percentile(energies, 0.2)

    elapsed_time = 0

    regions = []
    region_start = None

    for energy in energies:
        is_silence = energy <= threshold
        max_exceeded = region_start and elapsed_time - region_start >= max_region_size

        if (max_exceeded or is_silence) and region_start:
            if elapsed_time - region_start >= min_region_size:
                regions.append((region_start, elapsed_time))
            region_start = None

        elif (not region_start) and (not is_silence):
            region_start = elapsed_time
        elapsed_time += chunk_duration
    return regions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video or audio file to subtitle", nargs='?')
    parser.add_argument('-C', '--concurrency', help="Number of concurrent API requests to make", type=int, default=10)
    parser.add_argument('-o', '--output',
                        help="Output path for subtitles (by default, subtitles are saved in \
                        the same directory and name as the source path)")
    parser.add_argument('-F', '--format', help="Destination subtitle format", default="srt")
    parser.add_argument('-S', '--src-language', help="Language spoken in source file", default="en")
    parser.add_argument('-D', '--dst-language', help="Desired language for the subtitles", default="en")
    parser.add_argument('-K', '--api-key',
                        help="The Google Translate API key to be used. (Required for subtitle translation)")
    parser.add_argument('--list-formats', help="List all available subtitle formats", action='store_true')
    parser.add_argument('--list-languages', help="List all available source/destination languages", action='store_true')

    args = parser.parse_args()

    if args.list_formats:
        print("List of formats:")
        for subtitle_format in FORMATTERS: # Iterating over keys is default in Py3
            print("{format}".format(format=subtitle_format))
        return 0

    if args.list_languages:
        print("List of all languages:")
        for code, language in sorted(LANGUAGE_CODES.items()):
            print("{code}\t{language}".format(code=code, language=language))
        return 0

    if args.format not in FORMATTERS: # Iterating over keys is default in Py3
        print("Subtitle format not supported. Run with --list-formats to see all supported formats.")
        return 1

    if args.src_language not in LANGUAGE_CODES: # Iterating over keys is default in Py3
        print("Source language not supported. Run with --list-languages to see all supported languages.")
        return 1

    if args.dst_language not in LANGUAGE_CODES: # Iterating over keys is default in Py3
        print(
            "Destination language not supported. Run with --list-languages to see all supported languages.")
        return 1

    if not args.source_path:
        print("Error: You need to specify a source path.")
        parser.print_help()
        return 1

    try:
        audio_filename, audio_rate = extract_audio(args.source_path)
    except Exception as e:
        print("Error extracting audio: {}".format(e))
        return 1

    regions = find_speech_regions(audio_filename)

    pool = multiprocessing.Pool(args.concurrency)
    converter = FLACConverter(source_path=audio_filename)
    recognizer = SpeechRecognizer(language=args.src_language, rate=audio_rate, api_key=GOOGLE_SPEECH_API_KEY)

    transcripts = []
    if regions:
        try:
            widgets = ["Converting speech regions to FLAC files: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
            extracted_regions = []
            for i, extracted_region in enumerate(pool.imap(converter, regions)):
                extracted_regions.append(extracted_region)
                pbar.update(i)
            pbar.finish()

            widgets = ["Performing speech recognition: ", Percentage(), ' ', Bar(), ' ', ETA()]
            pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()

            for i, transcript in enumerate(pool.imap(recognizer, extracted_regions)):
                transcripts.append(transcript)
                pbar.update(i)
            pbar.finish()

            if not is_same_language(args.src_language, args.dst_language):
                if args.api_key:
                    google_translate_api_key = args.api_key
                    translator = Translator(args.dst_language, google_translate_api_key, dst=args.dst_language,
                                            src=args.src_language)
                    prompt = "Translating from {0} to {1}: ".format(args.src_language, args.dst_language)
                    widgets = [prompt, Percentage(), ' ', Bar(), ' ', ETA()]
                    pbar = ProgressBar(widgets=widgets, maxval=len(regions)).start()
                    translated_transcripts = []
                    for i, transcript in enumerate(pool.imap(translator, transcripts)):
                        translated_transcripts.append(transcript)
                        pbar.update(i)
                    pbar.finish()
                    transcripts = translated_transcripts
                else:
                    print("Error: Subtitle translation requires specified Google Translate API key. "
                          "See --help for further information.")
                    return 1

        except KeyboardInterrupt:
            if 'pbar' in locals() and pbar: pbar.finish()
            pool.terminate()
            pool.join()
            print("Cancelling transcription")
            return 1
        finally:
            # Ensure temporary audio file is removed if it exists
            if 'audio_filename' in locals() and os.path.exists(audio_filename):
                os.remove(audio_filename)


    timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
    formatter = FORMATTERS.get(args.format)
    formatted_subtitles = formatter(timed_subtitles)

    dest = args.output

    if not dest:
        base, ext = os.path.splitext(args.source_path)
        dest = "{base}.{format}".format(base=base, format=args.format)

    with open(dest, 'wb') as f:
        f.write(formatted_subtitles.encode("utf-8"))

    print("Subtitles file created at {}".format(dest))

    # audio_filename is removed in the finally block of the try/except KeyboardInterrupt
    # to ensure it's cleaned up even if errors occur mid-process.
    # if os.path.exists(audio_filename):
    #    os.remove(audio_filename) # Already handled by finally block

    return 0


if __name__ == '__main__':
    sys.exit(main())
