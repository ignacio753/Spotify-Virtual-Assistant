import socket
import time
import io
import click
import sys
import numpy as np
import cv2
from PIL import Image
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import face_recognition
import spotipy
import spotipy.util as util
import pyttsx3
import threading
from gtts import gTTS 
import os 
import threading

# The ID of the device where the songs will play
DEVICE_ID = ""
# Username of the spotify account where songs will play
USERNAME = ""
# Sets the permissions levels that the app can execute in the client system
SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

# Usere preferences configuration hash
# Controls the spotify's playlist, welcome message, language that will play for the recognized face.
# There should exist a '<name>.jpg" file in the root of the app, to be able to recognize the person
user_preferences = [
    {
        'name': 'ignacio',
        'playlist_id':'spotify:playlist:1JuZ3cL6DpvbxHdTI66134',
        'message': 'Bienvenido a casa Ignacio, reproducire tu playlist favorito',
        'lang': 'es'
    }
    ]

#command line arguments with 'click' lib
@click.command()
@click.option('--ip', default='192.168.20.250', show_default = True)
@click.option('--port', '-p', default='8888', type = int, show_default = True)
@click.option('--resolution', '-res', default='800x600', show_default = True)
@click.option('--freq', default = 10, show_default = True)
def main(ip, port, resolution, freq):
    # The face recognition algorythm must first parse the photos
    # Create known face encondings
    known_face_encodings = create_known_face_encodings()
    # Connect to spotify and return sp object
    sp = connect_to_spotify()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #info got from the user
        input = "ip: " + ip + " port: " + str(port) + " resolution: " + resolution + " frequency: " + str(freq)
        print(input)
		#connecting to the server socket
        s.connect((ip,int(port)))
		#frequency and resolution information to server
        toServer = "fps=" + str(freq) + "&resolution=" + str(resolution)
        print(toServer)
		#sending stuff
        s.send(addWhiteSpaces(toServer).encode())

        # Initialize a time counter, we will check for new faces every 3 seconds
        start_time = time.time()
        currently_playing = ''
        try:
            while 1:

                #######################################
                # Receiving the picture from the camera
                #receiving the size of the pictures
                data = s.recv(8)
                size = int.from_bytes( data, byteorder='little', signed=True)
                print(size)
                data = b''
                #reading the data
                while len(data) < size:
                    #receiving data in chunks because TCP..
                    packet = s.recv(size - len(data))
                    if packet:
                        data += packet
                #displaying thingies
                image = Image.open(io.BytesIO(data))
                cv_image = np.array(image)
                #we need to convert the picture to some kind of byte array. nasty stuff.
                cv_image = cv_image[:, :, ::-1].copy()

                ########################################
                # FACE Recognition and Spotify Logic
                # Calculate the elapsed time
                elapsed_time = time.time() - start_time
                # To not overload the app by calling the face recognition algorythm, we only call to 
                # check for new faces, every 3 seconds.
                if elapsed_time > 3:
                    currently_playing = recognize_faces(cv_image, known_face_encodings, sp, currently_playing)
                    # Re start the time counter
                    start_time = time.time()

                cv2.imshow('image', cv_image)
                cv2.waitKey(1)

        except (KeyboardInterrupt, SystemExit):
            #closing the window and the socket
            cv2.destroyAllWindows()
            s.close()
            print("socket closed")
            sys.exit()

# We authenticate the spotify app, and get the sp object that will allow us to
# do subsequent calls
def connect_to_spotify():
    token = util.prompt_for_user_token(USERNAME, SCOPE)
    if token:
        sp = spotipy.Spotify(auth=token)
        return sp
    else:
        print ("Fatal Error: Can't get token for spotify")

# Reads the images from the user preferences and creates the face encodings that are
# necccesary to perform the face recognition
def create_known_face_encodings():
    print("Doing face encodings...")
    face_encodings = []
    # Load pictures and learn how to recognize it.
    for user_preference in user_preferences:
        face_image = face_recognition.load_image_file(user_preference["name"] + ".jpg")
        # Extract the first face in the picture
        face_encoding = face_recognition.face_encodings(face_image)[0]
        face_encodings.append(face_encoding)
    # Array constains the encodings to do face recognition for all faces
    return face_encodings

# We tell the algorythm to check for known faces
# If a match is encounterd we play the user's welcome message and spotify's track
def recognize_faces(image, known_face_encodings, sp, currently_playing):
    face_encodings = face_recognition.face_encodings(image)
    for face_encoding in face_encodings:
        results = face_recognition.compare_faces(known_face_encodings, face_encoding)

        # A known face was encountered
        if True in results:
            # We look for the first match, this is determined by the algorythm, with the face
            # with the highest degree of confidence
            first_match_index = results.index(True)
            user_preference = user_preferences[first_match_index]
            name = user_preference['name']

            # If the song currently playing is from the 
            if currently_playing != name:
                play_user_song(sp, user_preference)
            return user_preference['name']
    return currently_playing

# Plays the user welcome message first and then starts the spotify playlist
def play_user_song(sp, person_preference):
    # If the spotify client is playing, stop so we can hear the welcome message
    if is_playing(sp):
        sp.pause_playback(device_id=DEVICE_ID)
    # Use the user prefered message and language
    myobj = gTTS(text=person_preference['message'], lang=person_preference['lang'], slow=False)
    # Same file is overwriten and play using the system call
    myobj.save("welcome.mp3")
    os.system("mpg321 welcome.mp3")
    # Start spotifys playback
    sp.start_playback(device_id=DEVICE_ID, context_uri=person_preference['playlist_id'], uris=None, offset=None)

# Checks if the client spotify is current in play mode
def is_playing(sp):
    return sp.current_playback()['is_playing'];

#adding whitespaces at the info for server so it can read the fix size of 30 chars
def addWhiteSpaces(param):
    param = str(param)
    for x in range(30 - len(str(param))):
        param += ' '
    return param

#diplaying the frame
def showimgfromdata(data, known_face_encodings, sp, elapsed_time, currently_playing):
   image = Image.open(io.BytesIO(data))

   cv_image = np.array(image)
   #we need to convert the picture to some kind of byte array. nasty stuff.
   cv_image = cv_image[:, :, ::-1].copy()

   if not is_playing(sp): #or elapsed_time > 3:
        currently_playing = recognize_faces(cv_image, known_face_encodings, sp, currently_playing)

   cv2.imshow('image', cv_image)
   cv2.waitKey(1)
   return currently_playing

if __name__ == "__main__":
    main()