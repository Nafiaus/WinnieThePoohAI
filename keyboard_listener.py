
import keyboard
import pyaudio
import os
import socket
import wave

# Twitch Variables
capReq = 'twitch.tv/commands'
server = 'irc.chat.twitch.tv'
port = 6667
channel = '#nafiaus'
nickname = 'nafiaus'
twitchOauth = os.eviron['NAFIAUS_KEY'] # get a token from twitchapps.com/tmi/

# Audio Variables
chunk = 1024
sampleFormat = pyaudio.paInt16
sampleRate = 44400
seconds = 10
audioChannels = 1
audioFilename = r'res\audio_recording.wav'  
running = True


twitch = socket.socket()
twitch.connect((server, port))
twitch.send(f'CAP REQ :{capReq}\n'.encode())
twitch.send(f'PASS {twitchOauth}\n'.encode())
twitch.send(f'NICK {nickname}\n'.encode())
twitch.send(f'JOIN {channel}\n'.encode())
print(f'joined {channel}')

while running:
    twitchraw = twitch.recv(4096).decode()
    if (twitchraw.find('PING') != -1):
        twitch.send(f'PONG :tmi.twitch.tv\n'.encode())
        print('ping pong')
    try:
        if(keyboard.is_pressed('f9')):
            print('initalizing...')
            recorder = pyaudio.PyAudio()
            stream = recorder.open(format=sampleFormat,
                channels=audioChannels,
                rate=sampleRate,
                input=True,
                frames_per_buffer=chunk
            )
            
            print('recording...')
            frames = []
            for i in range(0, int(sampleRate / chunk * seconds)):
                data = stream.read(chunk)
                frames.append(data)
                
            print('stopping...')
            stream.stop_stream()
            stream.close()
            recorder.terminate()
            
            print('saving...')
            with wave.open(audioFilename, 'wb') as saveSound:
                saveSound.setnchannels(audioChannels)
                saveSound.setsampwidth(recorder.get_sample_size(sampleFormat))
                saveSound.setframerate(sampleRate)
                saveSound.writeframes(b''.join(frames))
                saveSound.close()
            
            print('file saved.')
            twitch.send(f'PRIVMSG {channel} :!audio\n'.encode())
        else: # Do nothing
            pass
    except: # Do nothing
        pass
