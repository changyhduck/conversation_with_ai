# Introduction of this Project

This Project is an application for listening human's voice, and then convert it to text, and finally send the text into an AI model to get the answer, and then convert the answer into voice, and finally play the voice to user.

# User Interface
1. select a microphone
   - a dropdown list of all the microphones connected to the computer, and user can select one of them to use.
   - select a microphone and listen to the user's voice
2. select a speaker
   - a dropdown list of all the speakers connected to the computer, and user can select one of them to use.
   - select a speaker and play the answer to the user.
  
#Listening to User's Voice
1. when this program is running, it is always listening to the user's voice. 
2. this program will automatically recode the user's voice when it detects that the user is speaking. when the user stops speaking, the program will automatically stop recode.  

#Convert Voice to Text
1. after the program stops recoding the user's voice, it will automatically convert the voice to text, and then send the text to an AI model to get the answer.

#Convert Text to Voice
1. after the program gets the answer from the AI model, it will automatically convert the text to voice, and then play the voice to the user.
2. the program will automatically stop playing the voice when it detects that the user is speaking again.

#AI Model