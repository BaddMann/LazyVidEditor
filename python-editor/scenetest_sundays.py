#import datetime
#from datetime import datetime
import os, fnmatch
from collections import defaultdict
import sys, getopt
#from PIL import Image                                                                            
from datetime import datetime, timedelta
from subprocess import call

#import ffmpy
from moviepy.editor import *
#from timecode import Timecode

N = 1
today = datetime.today()
lastweek = datetime.today() - timedelta(days=N)
d = defaultdict(list)
#print today
Scenes = ["00:00:00"]
Files = []


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
def findscenes(thedate):
    #fnd out how to set datetime object on function...
    #thedate = datetime.date.today()
    Scenes = []
    with open(os.path.normpath('C:\Users\glencroftplay\AppData\Roaming\obs-studio\logs\infowriterlog.txt')) as f:
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
        os.system('convert ' +slidesname+str(edit)+'.png -flatten -gravity Center -crop 1280x620+0+0 -fuzz 10% -trim -resize 50% -trim '+slidesname+str(edit)+'_l3.png') ## Add Timeout to this somehow....
        ##### Also maybe run this imagemagick call in parellell, not serial...
        edit+=1

def quickedit(Scenes,Requests,Files,secssync):
    from timecode import Timecode
    logo_bug = "Z:\\CoF-Logo.png"
    timestr = datetime.today().strftime("%Y-%m-%d-%H-%M")
    slidesname = os.path.splitext(Files[1])[0]
    # print "Scenes: "+str(Scenes)
    # print "Requests: "+str(Requests)
    # print "Files: "+str(Files)
    #Testdata
    #Requests = [{'Title':'Testing', 'Person':'Higher Call','SubTitle':'Entertaining','startscene':11,'endscene':12, 'presentation':'third'},{'Title':'Testing2', 'Person':'Higher Call','SubTitle':'Entertaining','startscene':12,'endscene':13, 'presentation':'third'}]
    RequestNum = 0
    for request in Requests:
        if len(Requests) is RequestNum:
            break
        
        startscene=int(request.get('startscene'))
        endscene=int(request.get('endscene',"-1"))
        ta = Scenes[startscene] ## Retrieve Start TimeCode based on Slide Number
        tb = Scenes[endscene] ## Retrieve End TimeCode based on Slide Number (Should be a slide you don't want in Clip)
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
        slides_still = ImageClip(slidesname+str(startscene)+".png").set_duration(7)
        slides_video = VideoFileClip(Files[1]).subclip(ta, tb).fx(vfx.mask_color, [255, 255 ,255], thr=10, s=8).set_opacity(.7).set_pos('center').fx(afx.volumex, 0).fx(vfx.mask_color, [255, 255 ,255], thr=10, s=8).set_opacity(.7).set_pos('center')
        camera_video = VideoFileClip(Files[0]).subclip(cta, ctb).fx(afx.volumex,2)


        white_bg = ColorClip((camera_video.size),col=([255,255,255])).set_duration(camera_video.duration).set_opacity(.5)
        bug_clip = (ImageClip(logo_bug).resize(height=(camera_video.h*0.1)).set_pos(lambda t: (((camera_video.w*0.97)-bug_clip.w), ((t/camera_video.duration)*((camera_video.h)-(bug_clip.h)))) )
                    .set_duration(camera_video.duration).set_opacity(0.6).set_start(0)
                   )

        ### Dictate the Sype of Presentation the Slides should be presented as. 
        if presentation is "overlay":  
            # Composite the Layers of Video: Camera, 
            #                               whitebg (to make next layer viewable),
            #                               Slides (bg chromaed out and semi-transparent), 
            #                               Bug (on right side scaled and scrolling down to show length of clip.)
            result = CompositeVideoClip([camera_video, white_bg.crossfadein(1).crossfadeout(1), slides_video.crossfadein(1).crossfadeout(1), bug_clip])#.fadein(1).fadeout(1)
        elif presentation is "title":
            # Composite the Layers of Video: Camera, 
            #                               whitebg (to make next layer viewable),
            #                               still Slile (overlay for set seconds), 
            #                               Bug (on right side scaled and scrolling down to show length of clip.)
            result = CompositeVideoClip([camera_video, slides_still.crossfadein(1).crossfadeout(1), bug_clip])#.fadein(1).fadeout(1)
        elif presentation is "third":
            # Composite the Layers of Video: Camera, 
            #                               whitebg (to make next layer viewable),
            #                               Slides (bg chromaed out and semi-transparent),
            #                               Bug (on right side scaled and scrolling down to show length of clip.)
            lower_third = (ImageClip(slidesname+str(startscene)+"_l3.png").set_pos(lambda t:(("center",(camera_video.h*0.95)-(lower_third.h)))).set_duration(camera_video.duration*0.95))
            #lower_third = testofthird.set_pos(("center","bottom"))
            result = CompositeVideoClip([camera_video, lower_third.crossfadein(1).crossfadeout(1).set_opacity(.7), bug_clip])#.fadein(1).fadeout(1)

        video1path = os.path.dirname(Files[0])
        videofilenamepart1 = "".join(request.get('Title').split())
        videofilenamepart1 = videofilenamepart1.replace(":", "-")
        # print " Details: "+ videofilenamepart1, RequestNum
        result.write_videofile((video1path+"\\"+videofilenamepart1+"_Scene{0}-{1}.mp4".format(str(startscene), timestr)), 
					            write_logfile=False, 
					            codec='libx264', 
					            audio_codec='aac',
					            temp_audiofile=("scene{0}-temp-audio-{1}.m4a".format(str(startscene),timestr)), 
					            preset="ultrafast", 
					            remove_temp=True ) # Many options. ## .set_duration(8) ##test only 8 secs
        #with open((Files[0]+".txt"), "a") as myfile:
        #    myfile.append("file {0}\\{1}_Scene{2}-{3}.mp4".format(video1path,videofilenamepart1,str(startscene), timestr))

def allscenesarevalid(Scenes,Requests,Files,secssync):
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
    
Scenes = findscenes(today)
Files = find("*"+today.strftime('%Y-%m-%d')+"*.mp4", "Z:\\")
#Scenes = findscenes(lastweek)
#Files = find("*"+lastweek.strftime('%Y-%m-%d')+"*.mp4", "Z:\\")
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
quickedit(Scenes,Requests,Files,secssync)

#The Function that will join the clips by the specs of the requests. Needs to be fleashed out.
concatRequests(Scenes,Requests,Files)

os.system("pause")


## TODO: Create a Concat FFMPEG Command And Execute it (Funcation already named concatRequests())
##       Look into parsing new file created by q-systest.js

