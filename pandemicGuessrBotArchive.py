import discord
client = discord.Client()

# E265 block comment should start with '# '
import datetime
from random import randint
import os
import re

import keep_alive
import pandas as pd

import roman

from replit import db
import asyncio
from mods import getResultForDigit, map_nums

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)
    
def has_zh_numbers(inputString):
    for char in map_nums.keys():
        if char in inputString:
            return True
    return False
    
def roman_to_int_repl(match):
    return str(roman.fromRoman(match.group(0)))

def has_roman(inputString):
    return re.match(r'\b(?=[MDCLXVI]+\b)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b', inputString)

token = os.environ['DISCORD_BOT_SECRET']
channel_ids = (877202830065274941, 882982896934219817, 877202830065274941, "877202830065274941", 974679815401652245)

print(db['data'])
# print(db.keys())
@client.event
async def on_ready():
    print('Connected:', client.user)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    text = message.content
    if text == '講髒話是不是啊? 操場EEEEE萬公尺，開沙!!!!!!':
        await asyncio.sleep(10)
        await message.channel.send("來，我們口說好話，戴好口罩")
    if '今天' in text and message.channel.id in channel_ids and len(text)<15:
        today_num = int(''.join([s for s in text if s.isdigit()]))
        now = datetime.datetime.now()
        db['lastUpdateDate'] = now.day
        # db['todayReleased'] = False
        data = db['data']
        res_key, res_val = min(data.items(), key=lambda x: abs(today_num - int(x[1])))
        result = sorted(data.items(), key=lambda x: abs(today_num - int(x[1])))
        result = [(f"<@{i}>", j) for i, j in result]
        #db['data'] = {}
        await message.channel.send(f"<@{res_key}>'s guess was {res_val} and is the closest.")
        await message.channel.send("Today's Leaderboard:")
        await message.channel.send(pd.DataFrame(result).to_string(index=False, header=False))
        await message.channel.send(f"----------- ↓{(datetime.datetime.today()+datetime.timedelta(days=1)).strftime('%Y/%m/%d')}↓ -----------")
        data.clear()
        print(db['data'])
        db['data'].clear()
    elif ((has_numbers(text) or has_zh_numbers(text) or has_roman(text)) and message.channel.id in channel_ids) or text.startswith('^'):
        now = datetime.datetime.now()
        if (now.hour+8)%24>14:
            db['todayReleased'] = True
        else:
            db['todayReleased'] = False
        if not db['todayReleased'] or db['lastUpdateDate'] == now.day:
            if text.startswith('^'):
                text = text[1:]
            regex_p = re.compile(r'\b(?=[MDCLXVI]+\b)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b')
            text = (regex_p.sub(roman_to_int_repl, text))
            if has_zh_numbers(text):
                ID, Guess = str(message.author.id), getResultForDigit(text)
            else:
                ID, Guess = str(message.author.id), int(''.join([s for s in text if s.isdigit()]))
            if Guess < randint(10**8, 10**9):
                db['data'][ID] = Guess
                print(db['data'])
                await message.channel.send(f"User <@{ID}> has guessed {Guess}.")
        else:
            await message.channel.send("You cannot guess right now!")


try:
    keep_alive.keep_alive()
    client.run(token)
except discord.errors.HTTPException:
    print("\n\n\nBLOCKED BY RATE LIMITS\nTERMINATING NOW\n\n\n")
    os.system('kill 1')