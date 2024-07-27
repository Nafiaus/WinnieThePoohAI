This program is using Python Version 3.9

In Terminal do:

python -m pip install -U upgrade

python -m pip install -U playsound

python -m pip install -U openai

python -m pip install -U elevenlabs

python -m pip install -U pygame

setx OPENAI_API_KEY your_api_key_here

You then create an Capture Audio source listening to python.exe in OBS and a Window Capture listening for the title of your program (in this case "Winnie the Pooh AI"). Make sure to create a Chromakey Filter on the Window Capture to remove the green background.

You can change the gptRole to change the personality of the AI, change the winnieImage to of course change what they look like, and look through the ElevenLabs voices library to find a new voice. Copy the voice id and put it in winnieVoiceId
