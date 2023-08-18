
import cvlib    # high level module, uses YOLO model with the find_common_objects method
import cv2      # image/video manipulation, allows us to pass frames to cvlib
from argparse import ArgumentParser
import os
import sys
from datetime import datetime
from email.message import EmailMessage
from os import listdir
from os.path import isfile, join



# these will need to be fleshed out to not miss any formats
IMG_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tiff', '.gif']
VID_EXTENSIONS = ['.mov', '.mp4', '.avi', '.mpg', '.mpeg', '.m4v', '.mkv']

# used to make sure we are at least examining one valid file
VALID_FILE_ALERT = False
# if an error is dectected, even once. Used for alerts
ERROR_ALERT = False
#used for alerts. True if human found once
HUMAN_DETECTED_ALERT = False


# function takes a file name(full path), checks that file for human shaped objects
# saves the frames with people detected into directory named 'save_directory'
def humanChecker(video_file_name, save_directory, yolo='yolov4', nth_frame=15, confidence=.65, gpu=False):

    person_detection_counter = 0
    # for modifying our global variarble VALID_FILE
    global VALID_FILE_ALERT

    # tracking if we've found a human or not
    is_human_found = False
    analyze_error = False
    is_valid = False

    # we'll need to increment every time a person is detected for file naming

    # check if image
    if os.path.splitext(video_file_name)[1] in IMG_EXTENSIONS:
        frame = cv2.imread(video_file_name)  # our frame will just be the image
        # make sure it's a valid image

        if frame is not None:
            frame_count = 8   # this is necessary so our for loop runs below
            nth_frame = 1
            VALID_FILE_ALERT = True
            is_valid = True
            print(f'Image')
        else:
            is_valid = False
            analyze_error = True


    # check if video
    elif os.path.splitext(video_file_name)[1] in VID_EXTENSIONS:
        vid = cv2.VideoCapture(video_file_name)

        # get approximate frame count for video
        frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        #make sure it's a valid video
        if frame_count > 0:
            VALID_FILE_ALERT = True
            is_valid = True
            print(f'{frame_count} frames')
        else:
            is_valid = False
            analyze_error = True
    else:
        print(f'\nSkipping {video_file_name}')

    if is_valid:
        # look at every nth_frame of our video file, run frame through detect_common_objects
        # Increase 'nth_frame' to examine fewer frames and increase speed. Might reduce accuracy though.
        # Note: we can't use frame_count by itself because it's an approximation and could lead to errors
        for frame_number in range(1, frame_count - 6, nth_frame):

            # if not dealing with an image
            if os.path.splitext(video_file_name)[1] not in IMG_EXTENSIONS:
                vid.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                _, frame = vid.read()

            # feed our frame (or image) in to detect_common_objects
            try:

                bbox, labels, conf = cvlib.detect_common_objects(frame, model=yolo, confidence=confidence, enable_gpu=gpu)

            except Exception as e:
                print(e)
                analyze_error = True
                break

            if 'person' in labels:
                is_human_found = True

                for i in range(nth_frame):
                    person_detection_counter += 1
                    vid = cv2.VideoCapture(video_file_name)
                    vid.set(cv2.CAP_PROP_POS_FRAMES, frame_number+i)
                    _, frame = vid.read()
                    save_file_name = str(1000000 + person_detection_counter)+'.jpg'
                    cv2.imwrite(save_directory + '/' + save_file_name , frame)
                    if (frame_number+i)%100==0:
                        print(f'{frame_number+i} out of {frame_count}')

    return is_human_found, analyze_error





# takes a directory and returns all files and directories within
def getListOfFiles(dir_name):
    list_of_files = os.listdir(dir_name)
    all_files = list()
    # Iterate over all the entries
    for entry in list_of_files:
        # ignore hidden files and directories
        if entry[0] != '.':
            # Create full path
            full_path = os.path.join(dir_name, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(full_path):
                all_files = all_files + getListOfFiles(full_path)
            else:
                all_files.append(full_path)
    return all_files

def gen_video(dir_path):
    # Arguments
    #dir_path = 'bl14'
    ext = 'jpg'
    output  = video_file[:-4]+'_output.mp4'

    images = []
    for f in os.listdir(dir_path):
        if f.endswith(ext):
            images.append(f)

    # Determine the width and height from the first image
    image_path = os.path.join(dir_path, images[0])
    frame = cv2.imread(image_path)
    height, width, channels = frame.shape

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
    out = cv2.VideoWriter(output, fourcc, 30, (width, height))

    for image in images:
        image_path = os.path.join(dir_path, image)
        frame = cv2.imread(image_path)

        out.write(frame) # Write out frame to video
    out.release()


#############################################################################################################################
if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-d', '--directory', default='', help='Path to video folder')
    parser.add_argument('-f', default='', help='Used to select an individual file')
    parser.add_argument('--twilio', action='store_true', help='Flag to use Twilio text notification')
    parser.add_argument('--email', action='store_true', help='Flag to use email notification')
    parser.add_argument('--tiny_yolo', action='store_true', help='Flag to indicate using YoloV4-tiny model instead of the full one. Will be faster but less accurate.')
    # parser.add_argument('--continuous', action='store_true', help='This option will go through entire video file and save all frames with people. Default behavior is to stop after first person sighting.')
    parser.add_argument('--confidence', type=int, choices=range(1,100), default=65, help='Input a value between 1-99. This represents the percent confidence you require for a hit. Default is 65')
    parser.add_argument('--frames', type=int, default=15, help='Only examine every nth frame. Default is 10')
    parser.add_argument('--gpu', action='store_true', help='Attempt to run on GPU instead of CPU. Requires Open CV compiled with CUDA enables and Nvidia drivers set up correctly.')

    args = vars(parser.parse_args())

    # decide which model we'll use, default is 'yolov3', more accurate but takes longer
    if args['tiny_yolo']:
        yolo_string = 'yolov4-tiny'
    else:
        yolo_string = 'yolov4'


    #check our inputs, can only use either -f or -d but must use one
    if args['f'] == '' and args['directory'] == '':
        print('You must select either a directory with -d <directory> or a file with -f <file name>')
        sys.exit(1)
    if args['f'] != '' and args['directory'] != '' :
        print('Must select either -f or -d but can''t do both')
        sys.exit(1)


    every_nth_frame = args['frames']
    confidence_percent = args['confidence'] / 100

    gpu_flag = False
    if args['gpu']:
        gpu_flag = True

    # create a directory to hold snapshots and log file
    time_stamp = datetime.now().strftime('%m%d%Y%H%M%S')
    os.mkdir(f'D:\summarize\{time_stamp}')

    print('Beginning Detection')
    print(f'Directory {time_stamp} has been created')
    print(f"Email notifications set to {args['email']}. Text notification set to {args['twilio']}.")
    print(f"Confidence threshold set to {args['confidence']}%")
    print(f'Examining every {every_nth_frame} frames.')
    # print(f"Continous examination is set to {args['continuous']}")
    print(f"GPU is set to {args['gpu']}")
    print('\n\n')
    print(datetime.now().strftime('%m%d%Y-%H:%M:%S'))

    # open a log file and loop over all our video files
    with open(time_stamp + '/' + time_stamp +'.txt', 'w') as log_file:
        if args['f'] == '':
            video_directory_list = getListOfFiles(args['directory'] + '/')
        else:
            video_directory_list = [args['f']]

        # what video we are on
        working_on_counter = 1

        for video_file in video_directory_list:
            print(f'Examining {video_file}: {working_on_counter} of {len(video_directory_list)}: {int((working_on_counter/len(video_directory_list)*100))}%    ', end='')

            print(f'file = {video_file}, directory = {video_directory_list}')
            # check for people
            human_detected, error_detected = humanChecker(str(video_file), time_stamp, yolo=yolo_string, nth_frame=every_nth_frame, confidence=confidence_percent,  gpu=gpu_flag)

            if human_detected:
                HUMAN_DETECTED_ALERT = True
                print(f'Human detected in {video_file}')
                log_file.write(f'{video_file} \n')

            if error_detected:
                ERROR_ALERT = True
                print(f'\nError in analyzing {video_file}')
                log_file.write(f'Error in analyzing {video_file} \n' )

            working_on_counter += 1

            print('Generating Summarized video')
            gen_video(f'D:\summarize\{time_stamp}')
            print('Done!!!')

    if VALID_FILE_ALERT is False:
        print('No valid image or video files were examined')
    print(datetime.now().strftime('%m%d%Y-%H:%M:%S'))


# python file 'summerize.py' execution
# python summerize.py -f D:\summarize\ise_staffroom.mp4 --tiny_yolo
