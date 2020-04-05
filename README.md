# Spotify-Virtual-Assitance 

This project contains a proof of concept for a virtual digital assistance that uses artificial intelligence along with context awareness to recognize the face of the user and stream through Spotify their musical preference and a personalized welcome message in their language of choice.
The application uses an Axis Camera to transmit the images. 

The data from the camera is trasmited through sockets to a server machine that analyses the images coming from the live video feed. Then, with the help of machine learning, the application recognizes an already stored and pre-configured face from the list of known people. After the system has been able to identify a person, the app uses Google’s text to speech library to reproduce a welcoming message to the user, then using Spotify’s Web API the app also starts playing the songs from the user’s predefined playlist.

To run the client:
```sh
python3 client.py --ip 192.168.XX.XXX
```
To run the server:
```sh
create-package.sh mipsisa32r2el
eap-install.sh <target_ip> <password> install
eap-install.sh <target_ip> <password> start
```

