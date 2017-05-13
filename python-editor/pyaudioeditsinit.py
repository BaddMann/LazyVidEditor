import argparse
import os
import subprocess
import tempfile
import sys

ffmpegexec = "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"

def extract_audio(filename, channels=1, rate=16000, compress="yes"):
    temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    if not os.path.isfile(filename):
        print "The given file does not exist: {0}".format(filename)
        raise Exception("Invalid filepath: {0}".format(filename))
    if compress == "yes":
        command = [ffmpegexec, "-y", "-i", filename, "-ac", str(channels), "-af", "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2", "-ar", str(rate), "-loglevel", "error", temp.name]
    else:
        command = [ffmpegexec, "-y", "-i", filename, "-ac", str(channels), "-ar", str(rate), "-loglevel", "error", temp.name]

    subprocess.check_output(command)
    return temp.name, rate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="Path to the video file to edit", nargs='?')
    parser.add_argument('-m', '--minimum', help="minimum amount of seconds edit should be to be valid", type=int, default=10)
    parser.add_argument('-o', '--output',
                        help="Output path for edits (by default, subtitles are saved in \
                        the same directory and name as the source path)")
    parser.add_argument('-c', '--compress', help="Compress audio", default="yes")

    args = parser.parse_args()

    if not args.source_path:
        print("Error: You need to specify a source path.")
        return 1

    audio_filename, audio_rate = extract_audio(args.source_path)

    #################### Do something Fantastic here #########################################

    ##Put back when something fantastic is done.
    ##os.remove(audio_filename)

    return 0


if __name__ == '__main__':
    sys.exit(main())