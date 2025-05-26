#import datetime
#from datetime import datetime
import os, fnmatch
from collections import defaultdict
import sys, getopt
#from PIL import Image                                                                            
from datetime import datetime, timedelta
from subprocess import call
import json # Added for JSON configuration loading

#import ffmpy
from moviepy.editor import *
#from timecode import Timecode

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
}
config = DEFAULT_CONFIG.copy() # Start with defaults
try:
    # Try to determine the script's directory to make config file path more robust
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, CONFIG_FILE)
    with open(config_file_path, 'r') as f:
        config.update(json.load(f))
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
    print(f"Warning: Could not determine script directory to find {CONFIG_FILE}. Trying current directory. Using default configuration if not found.")
    try:
        with open(CONFIG_FILE, 'r') as f: # Fallback to current directory
            config.update(json.load(f))
        print(f"Loaded configuration from {CONFIG_FILE} (current directory)")
    except FileNotFoundError:
        print(f"Warning: {CONFIG_FILE} not found in current directory. Using default configuration.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode {CONFIG_FILE} from current directory. Using default configuration.")


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
    var = float(raw_input("Sync Seconds " +  str(videosyncoutput) + ": "))
    print "you entered", var
    return var

def userpromptsslides(timecodes):
    listofedits=[]
    howmanyedits =  int(raw_input("How Many edits are we performing? " ))
    print "Editing", howmanyedits, "times"
    return listofedits

def VideoSynccall(video1, video2):
    import alignment_by_row_channels
    video1path = os.path.dirname(video1)
    video1file = os.path.basename(video1)
    video2file = os.path.basename(video2)
    
    ##bad duration code
    #camera_video = VideoFileClip(video1file)
    #slides_video = VideoFileClip(video2file)
    #camdur = camera_video.duration
    #slidedur = slides_video.duration
    #diffdur = slidedur - camdur
    #print "Camera Duration " + str(camdur)
    #print "Slides Duration " + str(slidedur)
    #print "Slides minus Camera " + str(diffdur)
    
    if os.path.isfile(video1[0:-4] + "WAV.wav"):
        t = (0)
        return t
    t=alignment_by_row_channels.align(video1file,video2file,video1path)
    return t
   
def createpreview(Slides,Scenes,secssync):
    import json
    from timecode import Timecode
    addsecond = Timecode('60', '00:00:02:00')
    edit = 0
    slidesname = os.path.splitext(Slides)[0]
    for scene in Scenes:
        if "START" in scene:
            scene = "00:00:00"
        thetimecode = Timecode('60', scene+":00")
        endtimecode = thetimecode + addsecond
        endtimecode = (str(endtimecode).rsplit(':', 1))[0]
        aclip=VideoFileClip(Slides)
        if os.path.isfile(slidesname+str(edit)+".png"):
            print "files exist, exiting loop"
            break
        aclip.save_frame(slidesname+str(edit)+".png", t=endtimecode)#.fx(vfx.mask_color, [255, 255 ,255], thr=10, s=8)#.set_opacity(.7).set_pos('center')
        print "Created Preview PNG:", slidesname+str(edit)+".png"
        os.system('convert ' +slidesname+str(edit)+'.png -crop 1280x635+0+60 -trim -resize 30% '+slidesname+str(edit)+'_l3.png') ## Add Timeout to this somehow....
        ##### Also maybe run this imagemagick call in parellell, not serial...
        edit+=1

def quickedit(Scenes,Requests,Files,secssync, logo_bug_path_from_config, output_prefix_from_config):
    from timecode import Timecode
    # logo_bug = "Z:\\glencroft-logo.png" # Replaced by config
    logo_bug = logo_bug_path_from_config
    timestr = datetime.today().strftime("%Y-%m-%d-%H-%M")
    slidesname = os.path.splitext(Files[1])[0]
    # print "Scenes: "+str(Scenes)
    # print "Requests: "+str(Requests)
    # print "Files: "+str(Files)
    #Testdata
    #Requests = [{'Title':'Testing', 'Person':'Higher Call','SubTitle':'Entertaining','startscene':11,'endscene':12, 'presentation':'third'},{'Title':'Testing2', 'Person':'Higher Call','SubTitle':'Entertaining','startscene':12,'endscene':13, 'presentation':'third'}]
    RequestNum = 0
    
    # Ensure output directory exists
    if output_prefix_from_config:
        os.makedirs(output_prefix_from_config, exist_ok=True)
        print(f"Ensured output directory exists: {output_prefix_from_config}")

    for request in Requests:
        if len(Requests) is RequestNum:
            break
        
        startscene=int(request.get('startscene'))
        endscene=int(request.get('endscene',"-1"))
        
        # Check if scene numbers are valid
        if startscene >= len(Scenes) or (endscene != -1 and endscene >= len(Scenes)):
            print(f"Warning: Invalid scene numbers for request {request.get('Title')}. Start: {startscene}, End: {endscene}. Max scene index: {len(Scenes)-1}. Skipping this request.")
            RequestNum = RequestNum + 1
            continue
            
        ta = Scenes[startscene] ## Retrieve Start TimeCode based on Slide Number
        tb = Scenes[endscene] if endscene != -1 and endscene < len(Scenes) else Scenes[-1] # Ensure tb is valid
        
        print "ta is: ", ta
        tstc = Timecode('60', "00:00:"+str(int(abs(secssync)))+":00")
        if "00:00:00" in ta:
                ta = (str(tstc).rsplit(':', 1))[0]
                print "start time is now: "+ ta
        
        print "ta is: ", ta
        print str(tstc) + " sync differnece"
        if secssync > 0:
            
            tatc = Timecode('60', ta+":00") + tstc
            tbtc = Timecode('60', tb+":00") + tstc
        else:
            tatc = Timecode('60', ta+":00") - tstc
            tbtc = Timecode('60', tb+":00") - tstc
        cta = (str(tatc).rsplit(':', 1))[0]
        ctb = (str(tbtc).rsplit(':', 1))[0]
        if (str(tstc).rsplit(':', 1))[0] in ta: cta = "00:00:00"
        presentation = request.get('presentation')
        RequestNum = RequestNum + 1
        # print presentation


        #print "Camera Duration " + str(camera_video.duration)
        #print "Slide Duration " + str(slides_video.duration)
        print "Slide Time: " + ta + ", " + tb
        print "Camera Time: " + cta + ", " + ctb

        ### Create all the Layers needed (In code alone, video creation happens later)
        slides_still_path = slidesname+str(startscene)+".png"
        if not os.path.exists(slides_still_path):
            print(f"Warning: Preview image {slides_still_path} not found. Skipping this request or using placeholder.")
            # Optionally create a placeholder or skip
            # For now, let's assume createpreview was successful or this is handled
            # If we must have it, we could try to generate it here, or skip.
            # For now, we'll let ImageClip fail if it's critical.
            pass # Or handle missing still
            
        slides_still = ImageClip(slides_still_path).set_duration(7)
        slides_video = VideoFileClip(Files[1]).subclip(ta, tb).fx(vfx.mask_color, [255, 255 ,255], thr=10, s=8).set_opacity(.7).set_pos('center').fx(afx.volumex, 0).fx(vfx.mask_color, [255, 255 ,255], thr=10, s=8).set_opacity(.7).set_pos('center')
        camera_video = VideoFileClip(Files[0]).subclip(cta, ctb).fx(afx.volumex,2)


        white_bg = ColorClip((camera_video.size),col=([255,255,255])).set_duration(camera_video.duration).set_opacity(.5)
        
        if not os.path.exists(logo_bug):
            print(f"Warning: Logo bug image {logo_bug} not found. Bug will not be added.")
            bug_clip = None
        else:
            bug_clip = (ImageClip(logo_bug).resize(height=(camera_video.h*0.1)).set_pos(lambda t: (((camera_video.w*0.97)-bug_clip.w), ((t/camera_video.duration)*((camera_video.h)-(bug_clip.h)))) )
                        .set_duration(camera_video.duration).set_opacity(0.6).set_start(0)
                       )

        ### Dictate the Sype of Presentation the Slides should be presented as. 
        clips_to_composite = [camera_video]
        if presentation is "overlay":  
            clips_to_composite.extend([white_bg.crossfadein(1).crossfadeout(1), slides_video.crossfadein(1).crossfadeout(1)])
        elif presentation is "title":
            clips_to_composite.extend([slides_still.crossfadein(1).crossfadeout(1)])
        elif presentation is "third":
            lower_third_path = slidesname+str(startscene)+"_l3.png"
            if not os.path.exists(lower_third_path):
                print(f"Warning: Lower third image {lower_third_path} not found. Lower third will not be added.")
            else:
                lower_third = (ImageClip(lower_third_path).set_pos(lambda t:(("center",(camera_video.h*0.95)-(lower_third.h)))).set_duration(camera_video.duration*0.45))
                clips_to_composite.append(lower_third.crossfadein(1).crossfadeout(1).set_opacity(.7))

        if bug_clip:
            clips_to_composite.append(bug_clip)
            
        result = CompositeVideoClip(clips_to_composite)#.fadein(1).fadeout(1)
        
        # Construct output path
        video1path_original = os.path.dirname(Files[0]) # Keep original for reference or fallback
        videofilenamepart1 = "".join(request.get('Title').split())
        videofilenamepart1 = videofilenamepart1.replace(":", "-").replace("/", "-").replace("\\", "-") # Sanitize
        
        output_filename = f"{videofilenamepart1}_Scene{startscene}-{timestr}.mp4"
        
        if output_prefix_from_config:
            # Ensure prefix ends with a separator if it's a directory
            final_output_path = os.path.join(output_prefix_from_config, output_filename)
        else: # Fallback to original behavior if prefix is not set
            final_output_path = os.path.join(video1path_original, output_filename)
            
        print(f"Outputting to: {final_output_path}")

        result.write_videofile(final_output_path, 
                                write_logfile=False, 
                                codec='libx264', 
                                audio_codec='aac',
                                temp_audiofile=(os.path.join(output_prefix_from_config or ".", f"scene{startscene}-temp-audio-{timestr}.m4a")), 
                                preset="ultrafast", 
                                remove_temp=True )
        #with open((Files[0]+".txt"), "a") as myfile:
        #    myfile.append("file {0}\\{1}_Scene{2}-{3}.mp4".format(video1path,videofilenamepart1,str(startscene), timestr))

def allscenesarevalid(Scenes,Requests,Files,secssync):
                if not Scenes:
   allRequests = []
   entry = 0
   for Scene in Scenes:
    print "Scene is: " + str(entry) + " " + str(Scene)
    Request = {}
    Request['Title'] = "Scene " + str(entry) + " " + str(Scene)
    Request['Person'] = "Unknown"
    Request['SubTitle'] = "Unknown"
    Request['startscene'] = int(entry)
    Request['endscene'] = int(entry) + 1
    Request['presentation'] = "third"
    allRequests.append(Request)
    entry= entry +1
   #print allRequests
   return allRequests

def concatRequests(Scenes,Requests,Files):
    #Try to Concat the Files With the Text File Created in quickpreview function..... this is bad code.
    pass

# Use configuration for paths
obs_log_path = config.get("obs_infowriter_log", DEFAULT_CONFIG["obs_infowriter_log"])
video_search_path = config.get("video_search_path", DEFAULT_CONFIG["video_search_path"])
logo_bug_path_main = config.get("logo_bug_path", DEFAULT_CONFIG["logo_bug_path"])
output_path_prefix_main = config.get("output_path_prefix", DEFAULT_CONFIG["output_path_prefix"])

Scenes = findscenes(today, obs_log_path)
if not Files:
    Files = find("*"+today.strftime('%Y-%m-%d')+"*.mp4", video_search_path)
    if not Files:
        print(f"Warning: No video files found for today in {video_search_path}. Attempting last week.")
        Scenes = findscenes(lastweek, obs_log_path) # Update scenes for last week
        Files = find("*"+lastweek.strftime('%Y-%m-%d')+"*.mp4", video_search_path)
        if not Files:
            print(f"Error: No video files found for today or last week in {video_search_path}. Exiting.")
            # Potentially exit or handle gracefully
            sys.exit(1) # Exit if no files are found, as the rest of the script depends on them
    print("Files are in the Array Skipping find Step" if Files else "No files found.")

if not Files or len(Files) < 2:
    print("Error: Not enough video files found (expected at least Camera and Slides). Exiting.")
    sys.exit(1)
    
print "Processing Files:", str(Files[0]), ",", str(Files[1])
createpreview(Files[1], Scenes, 0) # This should Go after VideoSync, but it takes to long to process the sound, set sync to 0 for now
videosync=(0,0)
### foloowing code takes too long and value isn't where it should be, will revisit later. Default value of 0 used for now.
###videosync = VideoSynccall(Files[0],Files[1])
os.system('cls')
secssync = userpromptssync(videosync)
#listofedits = userpromptsslides(Scenes)
print "Camera Footage: " + Files[0]
print "Slides Footage: " + Files[1]
print "Syncing on this many seconds: ",secssync
print "TimeCodes that will be used: ", Scenes
#Loop Through All Scenes Function:
# 
Requests = []
#Temp Fix while testing that makes the script Go through Every secene, Once a GUI is in place, the requests will be more aimed.
Requests = allscenesarevalid(Scenes,Requests,Files,secssync)
del Requests[0]
del Requests[-1]
#del Requests[2]
#del Requests[3]

# Pass configured paths to quickedit
quickedit(Scenes,Requests,Files,secssync, logo_bug_path_main, output_path_prefix_main)

#The Function that will join the clips by the specs of the requests. Needs to be fleashed out.
# concatRequests(Scenes,Requests,Files) # This function is currently a pass

# --- Integration of log_parser ---
# This part was added in a previous step, ensure it uses robust paths if needed
# For example, if log_parser.py also needs config or if sample log path needs adjustment
# log_parser_input_file = "../Sampleoutput/2017-06-02_17-36-Slides.txt" # Path relative to this script's location
# print(f"\nAttempting to parse consolidated log file: {log_parser_input_file}")
# parsed_log_events = parse_log_file(log_parser_input_file)
# process_events_from_log_parser(parsed_log_events)
# --- End of log_parser integration ---


os.system("pause")


## TODO: Create a Concat FFMPEG Command And Execute it (Funcation already named concatRequests())
##       Look into parsing new file created by q-systest.js

# The log_parser integration block was here. It's being moved down to ensure
# it's one of the last things called, or integrated more deeply if its output is needed sooner.
# For now, just making sure it's after main video processing.

# --- Integration of log_parser (if still needed as a separate step) ---
# This section was previously added and is kept for now.
# It might be better to integrate its output into the main editing logic if applicable.
def process_events_from_log_parser(events_list):
    print("\n--- Events from Consolidated Log Parser ---")
    if not events_list:
        print("No events processed from consolidated log.")
        return

    for event in events_list:
        if event['event_type'] == 'MicUnmute':
            print(f"Potential Segment Start (Mic Active): {event['details']['mic_name']} at {event['timestamp']}")
        elif event['event_type'] == 'MicMute':
            print(f"Potential Segment End (Mic Inactive): {event['details']['mic_name']} at {event['timestamp']}")
        elif event['event_type'] == 'SceneChange':
            scene_name = event['details'].get('scene_name', 'N/A')
            obs_timecode = event['details'].get('obs_timecode', 'N/A')
            print(f"Scene Change Detected: {scene_name} at {event['timestamp']} (OBS Timecode: {obs_timecode})")
        elif event['event_type'] in ['RecordingStart', 'RecordingStop']:
            print(f"{event['event_type']} at {event['timestamp']}")
    print("-----------------------------------------\n")

# Path for parse_log_file: (assuming Sampleoutput is at repo root, and this script is in python-editor)
log_parser_input_file = "../Sampleoutput/2017-06-02_17-36-Slides.txt" 
# Check if the file exists before parsing
if os.path.exists(log_parser_input_file):
    print(f"\nAttempting to parse consolidated log file: {log_parser_input_file}")
    parsed_log_events = parse_log_file(log_parser_input_file)
    process_events_from_log_parser(parsed_log_events)
else:
    print(f"\nWarning: Consolidated log file for parser not found at {log_parser_input_file}. Skipping this step.")
# --- End of log_parser integration ---

# os.system("pause") # This may not be desirable in an automated script
print("Script finished.")