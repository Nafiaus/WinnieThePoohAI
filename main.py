# Grand Plan: 
#   - Create IRC connection to twitch.tv using sockets
#   - Listen for a !winnie command
#   - Using OpenAi API generate a text response flavored as Winnie the Pooh
#   - Using ElevenLabs API generate a voice response for OpenAI text
#   - Using Pygame animate a png of Winnie while talking
#   - Log everything to log file for future reference
#
# in terminal do:
# setx OPENAI_API_KEY your_api_key_here

import logging
import openai
import os
import pygame
import socket
import time

from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from playsound import playsound

os.environ['NAFIBOT_KEY'] = 'your twitchbot api key'
os.environ['ELEVEN_API_KEY'] = 'your elevenlabs api key'

# OpenAI Variables
gptModel = 'gpt-4o-mini'
gptRole = 'You are Winnie the Pooh, a soft teddy bear that is known for being naive and slow-witted. You are friendly and sometimes insightful and have a love for honey that can get you in trouble. You also happen to enjoy war tactics and will occasionally slip in some war tatics and outragous plans to take over the world. You will recieve messages formatted as: USERNAME "MESSAGE". Respond to the MESSAGE and use the users USERNAME in your response. Keep your response to 255 characters or lower.'
messageList = []

# Elevenlabs Variables
winnieModel = 'eleven_turbo_v2' # Fastest model I could find
winnieVoiceId = 'DfE5EkknFF950NR6OMui' # Bob voice
winnieVoiceStability = 0.3
winnieVoiceSimilarity = 0.2
voiceFile = 'winnie_voice.mp3'

# Twitch Variables
server = 'irc.chat.twitch.tv'
channel = '#' + 'desired channel name'
nickname = 'chatbot username'

# Canvas Variables
bgColor = (0, 255, 0) # Green
canvasSize = (1920, 1080)
canvasTitle = 'Winnie the Pooh AI'
winnieImage = pygame.image.load('winnie_the_pooh.png')
winnieX = 0
winnieY = 900
winniePos = (winnieX, winnieY)

running = True

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s = %(message)s',
                    datefmt='%Y-%m-%d :: %H:%M:%S',
                    handlers=[logging.FileHandler('chat.log', encoding='utf-8')]
)

# Method Definition Block
def log(msg): 
    logging.info(msg)
    print(msg)
    
def parseTwitchMessage(rawMessage):
    if (rawMessage.find('PRIVMSG') != -1):
        splitMessage = rawMessage.split('@')
        splitUsername = splitMessage[0].split('!')
        chatterUsername = splitUsername[1]
        privMessage = splitMessage[1].split(':')
        chatterMessage = privMessage[1]
        formattedLogMsg = f'{chatterUsername} : {chatterMessage}'
        log(formattedLogMsg)
        return([chatterUsername, chatterMessage])
    elif (rawMessage.find('PING') != -1):
        log('PING')
        twitch.send('PONG :tmi.twitch.tv'.encode())
        return(['twitch', 'ping'])
        
def sendBotMessage(message):
    twitch.send(f'PRIVMSG {channel} :{message}\n'.encode())

def newAIMessage(msg_role, new_message):
    formatted_message = {'role': msg_role, 'content': new_message}
    messageList.append(formatted_message)
    if (msg_role == 'assistant'):
        log(new_message)

# OPENAI INIT
newAIMessage('system', gptRole)

winnie = OpenAI()

# ELEVENLABS INIT
winnieAiVoice = ElevenLabs()

# PYGAME INIT
pygame.init()

canvas = pygame.display.set_mode(canvasSize)
pygame.display.set_caption(canvasTitle)
canvas.fill(bgColor)
canvas.blit(winnieImage, winniePos)
pygame.display.flip()

# TWITCH INIT
twitch = socket.socket()

twitch.connect((server, 6667))
twitch.send('CAP REQ :twitch.tv/commands\n'.encode())
twitch.send(f'PASS {os.environ["NAFIBOT_KEY"]}\n'.encode())
twitch.send(f'NICK {nickname}\n'.encode())
twitch.send(f'JOIN {channel}\n'.encode())

print(f'{nickname} has joined {channel}')

# MAIN LOOP
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    twitchRawResponse = twitch.recv(4096).decode()
    chatter = parseTwitchMessage(twitchRawResponse)
    
    if (chatter != None):
        if (chatter[1].lower().find("!winnie") != -1):
            newAIMessage('user', f'{chatter[0]} "{chatter[1]}"')
            
            aiResponse = winnie.chat.completions.create(
                model=gptModel,
                messages=messageList
            )
            
            aiMessage = aiResponse.choices[0].message.content
            sendBotMessage(aiMessage)
            newAIMessage('assistant', aiMessage)
            
            aiAudio = winnieAiVoice.generate(
                text=aiMessage,
                voice=Voice(
                    voice_id=winnieVoiceId,
                    settings=VoiceSettings(stability=winnieVoiceStability, similarity_boost=winnieVoiceSimilarity, use_speaker_boost=True)
                ),
                model=winnieModel
            )
            
            winniePos = (0, 500)
            canvas.fill(bgColor)
            canvas.blit(winnieImage, winniePos)
            pygame.display.update()
                
            save(aiAudio, voiceFile)
            playsound(voiceFile)
            os.remove(voiceFile)
            
            winniePos = (0, 900)
            canvas.fill(bgColor)
            canvas.blit(winnieImage, winniePos)
            pygame.display.update()

        pygame.display.update()
# END OF FILE
