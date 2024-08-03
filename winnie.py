#==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==
#
# Grand Plan: 
#   - Create IRC connection to twitch.tv using sockets
#   - Listen for a !winnie command
#   - Using OpenAi API generate a text response flavored as Winnie the Pooh to the winnie commandD
#   - Using ElevenLabs API generate a voice response for OpenAI text
#   - Using Pygame animate a png of Winnie while talking
#   - Log everything to log file for future reference
#
#==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==
#
#  Version Info:
#   - v.1 : Created Winnie
#   - v.2 : Added movement commands
#   - v.3 : Fixed logging. Added !discord, !countmessages, and !goodbye commands. Made winnie remember, and added a button to allow winnie to 
#               listen to mic 
#
#==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==
#
# Commands Implemented:
#   - !winnie
#   - !movewinnie
#   - !discord
#   - !countmessages
#   - !audio
#
#==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==<>==

import emoji
import io
import openai
import os
import pygame
import socket
import time

from datetime import datetime
from elevenlabs import Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from os import path
from playsound import playsound

# OpenAI Variables
gptModel = 'gpt-4o-mini'
gptRole = 'You are Winnie the Pooh, a soft teddy bear that is known for being naive and slow-witted. You are friendly and sometimes insightful and have a love for honey that can get you in trouble. You are well versed in video games like Call of Duty Mobile, Fortnite, Elden Ring, Mario 64,  You also happen to enjoy war tactics and will occasionally slip in some war tatics and outragous plans to take over the world. You will recieve messages formatted as: USERNAME "MESSAGE" : (optional) SYSTEM MESSAGE. Respond to the MESSAGE and use the users USERNAME in your response. Keep your response to 255 characters or lower. Do not use emojis'
messageList = []
gptOauth = os.environ['OPENAI_API_KEY'] # unused just here to show that you need an enviroment variable with this name set to your api key
whisperModel = 'whisper-1'

# Elevenlabs Variables
winnieModel = 'eleven_turbo_v2'
winnieVoiceId = 'DfE5EkknFF950NR6OMui'
winnieVoiceStability = 0.3
winnieVoiceSimilarity = 0.2
voiceFile = r'res\winnie_voice.mp3'
elevenOauth = os.environ['ELEVEN_API_KEY'] # unused just here to show that you need an enviroment variable with this name set to your api key

# Twitch Variables
capReq = 'twitch.tv/commands'
server = 'irc.chat.twitch.tv'
port = 6667
channel = '#nafiaus'
nickname = 'nafibot'
twitchOauth = os.environ['NAFIBOT_KEY'] # get a token from twitchapps.com/tmi/

# Canvas Variables
bgColor = (0, 255, 0)
canvasSize = (1920, 1080)
canvasTitle = 'Winnie the Pooh AI'
winnieImage = pygame.image.load(r'res\winnie_the_pooh.png')
bottomY = 875
bottomUpY = 500
bottomLeftX = 0
bottomMiddleX = 700
bottomRightX = 1350
winniePos = (bottomLeftX, bottomY)
winniePosInt = 0
running = True

# Misc Variables
messageListFile = r'log\messagelist.txt'
audioFilename = r'res\audio_recording.wav'
discordLink = 'https://discord.gg/McMJRZhnCx'
seperatorChar = '\n'

# OPENAI INIT
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

twitch.connect((server, port))
twitch.send(f'CAP REQ :{capReq}\n'.encode())
twitch.send(f'PASS {twitchOauth}\n'.encode())
twitch.send(f'NICK {nickname}\n'.encode())
twitch.send(f'JOIN {channel}\n'.encode())

print(f'{nickname} has joined {channel}')
print(f'{twitch.recv(4096).decode()}')

# Method Definition Block
def disconnectWinnie():
    newAIMessage('user', 'chat "Tell us goodbye"')
    moveIt()
    saveMessageList()
    running = False
    
def saveMessageList():
    if (os.path.exists(messageListFile)):
        os.remove(messageListFile)
    with open(messageListFile, 'x') as fp:
        messageListStr = seperatorChar.join(map(str, messageList))
        formattedMessageListStr = emoji.replace_emoji(messageListStr, replace='')
        fp.write(formattedMessageListStr)

def loadMessageList():
    with open(messageListFile, 'r') as fp:
        rawMessageList = fp.read()
        messageList = rawMessageList.split(seperatorChar)
    
def log(username, message):
    formattedMessage = emoji.replace_emoji(message, replace='')
    now = datetime.now()
    formattedTime = now.strftime('%Y-%m-%d %H:%M:%S')
    filename = f'log\\{username}.txt'
    if not (os.path.exists(filename)):
        with open(filename, 'w') as fp:
            print(f'{filename} created')
    with open(filename, 'a') as fp:
        fp.write(f'{formattedTime} {formattedMessage}')
    print(f'{username} : {message}')
    
def countMessages(username):
    filename = f'log\\{username}.txt'
    if (os.path.exists(filename)):
        with open(filename, 'r') as fp:
            content = fp.read()
            lineList = content.split('\n')
            lines = 0
            for i in lineList:
                if i:
                    lines += 1
            return lines
    else:
        return -1

def parseTwitchMessage(rawMessage):
    print(rawMessage)
    if (rawMessage.find('PRIVMSG') != -1):
        splitMessage = rawMessage.split('@')
        splitUsername = splitMessage[0].split('!')
        chatterUsername = splitUsername[1]
        privMessage = splitMessage[1].split(':')
        chatterMessage = privMessage[1]
        formattedLogMsg = f'{chatterUsername} : {chatterMessage}'
        log(chatterUsername, chatterMessage)
        return([chatterUsername, chatterMessage])
    elif (rawMessage.find('PING') != -1):
        log('twitch', 'PING')
        twitch.send('PONG :tmi.twitch.tv\n'.encode())
            
def sendBotMessage(message):
    twitch.send(f'PRIVMSG {channel} :{message}\n'.encode())
    
def newAIMessage(msg_role, new_message):
    formatted_message = {'role': msg_role, 'content': new_message}
    messageList.append(formatted_message)
    saveMessageList()
    if (msg_role == 'assistant'):
        log('winnieai', new_message)

def moveIt():
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
            settings=VoiceSettings(
                stability=winnieVoiceStability,
                similarity_boost=winnieVoiceSimilarity,
                use_speaker_boost=True
            )
        ),
        model=winnieModel
    )
    if (winniePosInt == 0):
        winniePos = (bottomLeftX, bottomUpY)
    elif (winniePosInt == 1):
        winniePos = (bottomMiddleX, bottomUpY)
    elif (winniePosInt == 2):
        winniePos = (bottomRightX, bottomUpY)
        
    canvas.fill(bgColor)
    canvas.blit(winnieImage, winniePos)
    pygame.display.update()
                
    save(aiAudio, voiceFile)
    playsound(voiceFile)
    os.remove(voiceFile)
    
    if (winniePosInt == 0):
        winniePos = (bottomLeftX, bottomY)
    elif (winniePosInt == 1):
        winniePos = (bottomMiddleX, bottomY)
    elif (winniePosInt == 2):
        winniePos = (bottomRightX, bottomY)
        
    canvas.fill(bgColor)
    canvas.blit(winnieImage, winniePos)
    pygame.display.update()
    
def transcribeAudio():
    audioWav = open(audioFilename, 'rb')
    transcription = winnie.audio.transcriptions.create(
        model=whisperModel,
        file=audioWav
    )
    audioWav.close()
    print(transcription.text)
    os.remove(audioFilename)
    newAIMessage('user', f'nafiaus "{transcription.text}"')
    moveIt()
    
# Load Messages into system or program personality
if not (os.path.exists(messageListFile)):
    newAIMessage('system', gptRole)
else:
    loadMessageList()

# MAIN LOOP
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    twitchRawResponse = twitch.recv(4096).decode()
    chatter = parseTwitchMessage(twitchRawResponse)
    
    if (chatter != None):
        chatterUsername = chatter[0].lower()
        chatterMessage = chatter[1].lower()
        if (chatterMessage.find('cheap viewers') != -1): # Cheap Viewers Bot Detector
            sendBotMessage(f'/ban {chatterUsername}')
            newAIMessage('user', f'nafiaus "You have just banned a bot named {chatterUsername}."')
            moveIt()
            
        elif (chatterMessage.find('!winnie') != -1): # Winnie Command
            newAIMessage('user', f'{chatter[0]} "{chatter[1]}"')
            moveIt()
            
        elif (chatterMessage.find('just subscribed for') != -1): # Just Subscribed
            if (chatterUsername.lower() == 'nafiaus'):
                firstSplit = chatterMessage.split('for ')
                secondSplit = firstSplit[1].split(' in')
                thirdSplit = firstSplit[0].split(' just')
                timeSubbed = secondSplit[0]
                userSubbed = thirdSplit[0]
                newAIMessage('user', f'nafiaus "This is a special message because {userSubbed} just subscribed to nafiaus\' twitch channel for {timeSubbed} in a row!"')
                moveIt()
            elif (chatterUsername != 'nafiaus'):
                newAIMessage('user', f'nafiaus "You need to scold {chatterUsername} for trying to fake subscribing and fooling you"')
                moveIt()
                
        elif (chatterMessage.find('!movewinnie') != -1): # Move Winnie Command
            wordList = chatterMessage.split(' ')
            print(wordList)
            if (len(wordList) > 1):
                if (wordList[1].rstrip() == 'right'):
                    if (winniePosInt == 2):
                        newAIMessage('user', f'{chatterUsername} "I have tried moving you to the right position of nafiaus\' stream, but you are already there" : tell them that when they move you it needs to be a position you are not in already')
                        moveIt()
                    elif (winniePosInt != 2):
                        winniePosInt = 2
                        newAIMessage('user', f'{chatterUsername} "I have moved you to the right position of nafiaus\' stream"')
                        moveIt()
                elif (wordList[1].rstrip() == 'middle'):
                    if (winniePosInt == 1):
                        newAIMessage('user', f'{chatterUsername} "I have tried moving you to the middle position of nafiaus\' stream, but you are already there" : tell them that when they move you it needs to be a position you are not in already')
                        moveIt()
                    elif (winniePosInt != 1):
                        winniePosInt = 1
                        newAIMessage('user', f'{chatterUsername} "I have moved you to the middle position of nafiaus\' stream"')
                        moveIt()
                elif (wordList[1].rstrip() == 'left'):
                    if (winniePosInt == 0):
                        newAIMessage('user', f'{chatterUsername} "I have tried moving you to the left position of nafiaus\' stream, but you are already there" : tell them that when they move you it needs to be a position you are not in already')
                        moveIt()
                    elif (winniePosInt != 0):
                        winniePosInt = 0
                        newAIMessage('user', f'{chatterUsername} "I have moved you to the left position of nafiaus\' stream"')
                        moveIt()
                elif (wordList[1].rstrip() != 'left' or 'middle' or 'right'):
                    newAIMessage('user', f'{chatterUsername} "I have moved you to a position of nafiaus\' stream that does not exist" : tell them that they must specify "left", "middle", or "right"')
                    moveIt()
            elif (len(wordList) == 1):
                newAIMessage('user', f'{chatterUsername} "I have tried moving you nowhere" : tell them that they must specify "left", "middle", or "right"')
                moveIt()
                
        elif (chatterMessage.find('!discord') != -1): # Discord Command
            sendBotMessage(f'Make sure to leave a thumbs up reaction in the #rules: {discordLink}')
            newAIMessage('user', f'{chatterUsername} "tell me to check the chat for the discord link and to leave a thumbs up reaction in the rules channel so that I don\'t get kicked"')
            moveIt()
            
        elif (chatterMessage.find('!countmessages') != -1): # Count Messages Command
            wordList = chatterMessage.split(' ')
            count = countMessages(chatterUsername)
            if (count == -1):
                newAIMessage('user', f'{chatterUsername} "Tell me that I do not exist in the logs somehow and cannot get the count of my messages."')
                moveIt()
            else:
                newAIMessage('user', f'{chatterUsername} "Tell me that I have {count} messages sent in Nafiaus\' Twitch Channel."')
                moveIt()
                    
        elif (chatterMessage.find('!goodbye') != -1): # Goodbye Command
            if (chatterUsername == 'nafiaus'):
                disconnectWinnie()
            else:
                newAIMessage('user', f'{chatterUsername} "Tell me that only Nafiaus can make you leave the chat."')
                moveIt()
        
        elif (chatterMessage.find('!audio') != -1): # Check for Audio Recording to Transcribe
            if (os.path.exists(audioFilename)):
                transcribeAudio()
            else:
                newAIMessage('user', f'{chatterUsername} "Tell me that Nafiaus has not asked [you] a question yet."')
                moveIt()
                
# END OF FILE
