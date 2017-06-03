#import datetime
import os, fnmatch
from collections import defaultdict
from PIL import Image                                                                                
from datetime import datetime, timedelta

#import ffmpy
from moviepy.editor import *
#from timecode import Timecode

##### Works Very well! pyAudioAnalysis
##### C:\Users\glencroftplay\Documents\GitHub\pyAudioAnalysis>python audioAnalysis.py silenceRemoval -i C:\Users\glencroftplay\test.wav --smoothing 3.0 --weight 0.05

### TransCode:
############## C:\Users\glencroftplay\Documents\GitHub\pyAudioAnalysis>ffmpeg -i Z:\2017-01-23-VarietyShow.mp4 -af "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2" -vn -ac 1 -ar 8000 Z:\2017-01-23-VarietyShow.wav


N = 7
today = datetime.today()
lastweek = datetime.today() - timedelta(days=N)
d = defaultdict(list)
#print today
Scenes = []
Files = []


####Define Functions Here:
def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result

#####Make this a Function...
def findscenes(thedate):
    #fnd out how to set datetime object on function...
    #thedate = datetime.date.today()
    Scenes = []
    with open(os.path.normpath('C:\Users\glencroftplay\AppData\Roaming\obs-studio\logs\infowriterlog.txt')) as f:
        for line in f:
            #print line
            if thedate.strftime('%Y-%m-%d') in line:
                for line in f:  # now you are at the lines you want
                    if thedate.strftime('%Y-%m-%d') in line:
                        break
                    # do work
                    if 'Scene' in line:
                        fields = line.split('-')
                        #print fields
                        Scenes.append(fields[0].strip())
        return Scenes

def userpromptssync(videosyncoutput):
    var = float(raw_input("Sync Seconds " +  str(videosyncoutput) + ": "))
    print "you entered", var
    return var

def userpromptsslides(timecodes):
    listofedits=[]
    #howmanyedits =  int(raw_input("How Many edits are we performing? " ))
    #print "Editing", howmanyedits, "times"
    return listofedits

def VideoSynccall(video1, video2):
    import alignment_by_row_channels
    video1path = os.path.dirname(video1)
    video1file = os.path.basename(video1)
    video2file = os.path.basename(video2)
    t=alignment_by_row_channels.align(video1file,video2file,video1path)
    return t
   
def showpreview(Slides,Scenes,secssync):
    from timecode import Timecode
    addsecond = Timecode('60', '00:00:02:00')
    edit = 0
    slidesname = os.path.splitext(Slides)[0]
    for scene in Scenes:
        edit+=1
        thetimecode = Timecode('60', scene+":00")
        endtimecode = thetimecode + addsecond
        endtimecode = (str(endtimecode).rsplit(':', 1))[0]
        aclip=VideoFileClip(Slides)
        if os.path.isfile(slidesname+str(edit)+".jpg"):
            print "files exist, exiting loop"
            break
        aclip.save_frame(slidesname+str(edit)+".jpg", t=endtimecode)
        print "Created Preview JPEG:", slidesname+str(edit)+".jpg"

def quickedit(Scenes,Requests,Files,secssync):
    logo_bug = "Z:\\CoF-Logo.png"
    timestr = datetime.date.today().strftime("%Y-%m-%d-%H-%M")
    #Testdata
    Requests = [{'Title':'God at Work', 'Person':'Marvin and Vi Miller','SubTitle':'Going to Hawaii','startscene':17,'endscene':18, 'presentation':'title'},{'Title':'Message', 'Person':'Joel Eidsness','SubTitle':'Faithfulness...The Music of the Gospel','startscene':24,'endscene':43, 'presentation':'overlay'}]

    for request in Requests:
        startscene=request.get('startscene')
        endscene=request.get('endscene')
        ta = Scenes[startscene]
        tb = Scenes[endscene]
        print ta
        print tb


        slides_video = VideoFileClip(Files[1]).subclip(ta,tb)
        camera_video = VideoFileClip(Files[0]).subclip(ta,tb).fx(afx.volumex,2)


        slides_video2 = (slides_video.fx( vfx.mask_color, [255,255,255],thr=10,s=8)
                        .set_opacity(.7) # whole clip is semi-transparent
                        .set_pos('center')
				        .fx(afx.volumex,0)
				        )
				   
        white_bg = ColorClip((camera_video.size),col=([255,255,255])).set_duration(camera_video.duration).set_opacity(.5)
        #bug_clip = (ImageClip(logo_bug).resize(height=(camera_video.h*0.1)).set_pos(lambda t: (((camera_video.w*0.99)-bug_clip.w), ((t/camera_video.duration)*((camera_video.h)-(bug_clip.h)))) )
        #            .set_duration(camera_video.duration).set_opacity(0.6).set_start(1)
        #           )

        result = CompositeVideoClip([camera_video, white_bg, slides_video2]).fadein(1).fadeout(1) # Overlay text on video

        video1path = os.path.dirname(Files[0])
        result.write_videofile((video1path+"\\Test_edited-{0}.mp4".format(timestr)), 
					            write_logfile=False, 
					            codec='libx264', 
					            audio_codec='aac',
					            temp_audiofile=("temp-audio-{0}.m4a".format(timestr)), 
					            preset="ultrafast", 
					            remove_temp=True ) # Many options.


#Scenes = findscenes(today)
#Files = find("*"+today.strftime('%Y-%m-%d')+"*.mp4", "Z:\\")
Scenes = findscenes(lastweek)
Files = find("*"+lastweek.strftime('%Y-%m-%d')+"*.mp4", "Z:\\")
print "Processing Files:", str(Files[0]), ",", str(Files[1])
videosync = VideoSynccall(Files[0],Files[1])
os.system('cls')
secssync = userpromptssync(videosync)
showpreview(Files[1], Scenes, secssync)
listofedits = userpromptsslides(Scenes)
print "Camera Footage: " + Files[0]
print "Slides Footage: " + Files[1]
print "Syncing on this many seconds: ",secssync
print "TimeCodes that will be used: ", Scenes
Requests={}
quickedit(Scenes,Requests,Files,secssync)

os.system("pause")








############### Moviepy Not Working on Windows yet also missing Imagemagic, it's installed
#
#clip = VideoFileClip("C:\\Users\\glencroftplay\\Downloads\\Slides.mp4").subclip(Scenes[2],Scenes[3])

# Generate a text clip. You can customize the font, color, etc.
#txt_clip = TextClip("Testing 1",fontsize=70,color='white')

# Say that you want it to appear 10s at the center of the screen
#txt_clip = txt_clip.set_pos('center').set_duration(10)

# Overlay the text clip on the first video clip
#video = CompositeVideoClip([clip])

#video.write_videofile("myHolidays_edited.avi",fps=24, codec='mpeg4')



