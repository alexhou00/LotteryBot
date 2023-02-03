import discord
client = discord.Client()

import datetime
from random import sample, gauss, randint
from time import time
from collections import Counter, deque
import os
import re
from discord.ext import tasks
from math import log, ceil, exp  # log() = log_e() = ln()
from math import e as math_e
import matplotlib.pyplot as plt
import csv
# import sys
from itertools import chain
import subprocess

import keep_alive

# import pandas as pd
# import pdfkit
import openpyxl

import logging

from replit import db

# to do: $buy (quick pick, pm, ling2gu3, 數值自動監控 and notif,收盤, 購入價, dowjones
# future to do: BLACKJACK
# done: receipt csv[done], one xlsx), self edit stonks, reply users instead of tags, stock permanent history

token = os.environ['DISCORD_BOT_SECRET']

# disable all imported modules logging
for name, logger in logging.root.manager.loggerDict.items():
    logger.disabled=True
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.DEBUG)

# define channels
test_channel = 882982896934219817  # LANG-test
secret_channel = 1068798588622225418  # fig.png channel
GUESS_channel = 1067835837397618758  # main channel (in GUESS?)
geo_channel = 968951342456537138  # bot-commands
channel_ids = (test_channel, GUESS_channel, geo_channel)

# define constants
LOTTERY_COST = 2
DAILY_INCOME = 100

tradeStockCount = 4  # count loop to check if time to trade stock (every 6 loops currently)
        
# also another prizeTable in tasks.loop if this one here is edited
prizeTable = [0, 2, 6, 10, 600, 60000, 10000000]
KEYPAD_TABLE = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')

STARTUP_NAMES = [("fintech","FTK"),
                ("ShareExchange","SXG"),
                ("Xylitol","XLT"),
                ("Kompound","KPD"),
                ("Richtig","RTG"),
                ("Benoît B. Mandelbrot", "BBM"),
                 
                ("ForYourInvestments","FYI"),
                ("Recombinase-Mediated Cassette","RMC"),
                ("BLÅHAJ","BLH"),
                ("Apricot","APRC"),
                ("Enyzme","EYZ"),
                ("Miquel Point Corp.","MPC"),
                ("FinancialFlightStock","FFS"),
                ("ᴄᴏᴍᴍᴜᴛᴇx", "COM"),
                ("I'llLuminatE","ILE"),
                ("NeverMind", "NVM"),
                ("Neosoft", "NSF")]


# stockHistory = [[] for i in db['stockmarket']]  # len stockHistory = len db['stockmarket']
# make sure stockHistory has same length of stockmarket when new stock created
# so that stockHistory could track stock's history (they're the same index)
if len(db['stockHistory']) < len(db['stockmarket']):
    for i in range(len(db['stockmarket'])-len(db['stockHistory'])):
        db['stockHistory'].append([])

# db['stockDetails']['editCooldown'] = 0
# db['stockDetails']['editCooldown'] = 0
# view database info first
logging.debug("Database: " + str(db.keys()))
for k, v in db.items():
    if isinstance(v, str):
        logging.debug(f"{k}: {type(v)} value- {v}")
    else:         
        try:
            iterator = iter(v)
        except:
            logging.debug(f"{k}: {type(v)} value- {v}") # is not iterable
        else:
            if isinstance(v, float):
                pass
            else:
                # is iterable
                try:
                    logging.debug(f"{k}: {(type(v).__name__).split('.')[-1]} length- {len(v)}; bytes- {list(chain(*v)).__sizeof__()}") # is nested iterable
                except:
                     logging.debug(f"{k}: {(type(v).__name__).split('.')[-1]} length- {len(v)}; bytes- {list(v).__sizeof__()}") # is iterable
                    

## DELETE THINGS HERE 
##

stockEditNum = 0

def register(ID):  # user auto register / join the bank system
    db['bank'][ID] = 100
    db['guesses'][ID] = list()

@tasks.loop(seconds=10)  # repeat after every 10 seconds
async def checkIfLotteryDraw():  # just loop idc the names
    global tradeStockCount, prizeTable, stockEditNum # , stockHistory
    tradeStockCount += 1  # % 6 == 0 to trade stocks
    hour = (datetime.datetime.now().hour + 8) % 24  # utc +8
    if (hour % 2 == 0 and hour != 4 and hour != 6) and hour != db['prevLotDrawHr']:
    #if True:
        if hour == 0:  # if 12 o clock utc+8
            db['daily'] = []
        db['prevLotDrawHr'] = hour # has already drawed this 期
        results = sorted(sample(range(1,43), 6))  # random pick
        
        channel = client.get_channel(GUESS_channel)
        times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)  # 202300xx
        await channel.send(f"第 {times} 期開獎結果：**{' '.join([str(i).zfill(2) for i in results])}**")
        db['times'] += 1  # next 期  ## IMPORTANT ##
        q = db['Quantity']  # count how many purchases (everyone in total)
        db['Quantity'] = 0
        times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)
        await client.change_presence(activity=discord.Game(name=f"第 {times} 期")) # switch to playing next 期

        if q > 100:
            x = 100/(math_e-1)  # tmp var
            prizeTable = [0, 2, 6, ceil(10*log(q/x+1)), ceil(600*log(q/x+1)), ceil(60000*log(q/x+1)), ceil(10000000*log(q/x+1))]  ## Another prizeTable def above
            # P = [2,6,10r,600r, 60000r, 10000000r] as of 20230128
            # r = \max (1,\log_{e}(\frac{Q}{\frac{100}{e-1}}+1))
            await channel.send(f"本期所有人共買了 {q} 張，因此對中三個以上的獎金將個別乘上 {round(log(q/x+1),9)} 並無條件進位至整數，而獎金陣列 P = {prizeTable[1:]}，買氣越旺獎金越高！")

        wb = openpyxl.Workbook()  # excel file (wb: workbook == file)
        ws = wb.active  # current WorkSheet (default named Sheet)
        header = ["序號", "#1", "#2", "#3", "#4", "#5", "#6", "對中數目", "獎金"] 
        ws.append(header)
        
        for person, guesses in db['guesses'].items():  # for person in all guesses (Person==ID, type:str)
            # countList = []  # deprecated in my code: count 對中幾個 each guess and store each guess (row) here
            countSum = 0  # prize sum
            # csvList = []  # list to create csv (deprecated??)
            ws.append([f"User {person}"])
            for n, guess in enumerate(guesses):  # for each guess of a person in that person's guesses
                count = sum(number in results for number in guess)  # count how many True's
                db['bank'][person] += prizeTable[count]
                # countList.append(count)
                # csvList.append( [n+1] + list(guess) + [count, prizeTable[count]])
                row = [n+1] + list(guess) + [count, prizeTable[count]]
                ws.append(row)
                countSum += prizeTable[count]  # add to prize sum
            # end for
            ws.append([f"總共 ${countSum}"])
            ws.append([])


            if len(guesses) == 1:  # if this person only purchased one lottery
                await channel.send(
                    f"<@{person}> 對中了 {count} 個數字並贏得了 ${prizeTable[count]}，現在他有 ${db['bank'][person]}。")

            else:   # he/she purchased more than one lottery
                await channel.send(f"<@{person}> 買了 {len(guesses)} 張並總共贏得了 ${countSum}，詳細結果請見附檔，現在他有 ${db['bank'][person]}。")
        # end for

                        
        wb.save('files/report.xlsx')
        await channel.send(file=discord.File('files/report.xlsx'))
        os.remove('files/report.xlsx')



        if len(db['guesses']) != 0: await channel.send(f"以上就是本期的開獎！")
        else: await channel.send("本期沒有人下注...")
        db['guesses'] = {}
        

    # STONKS REFRESH
    if tradeStockCount % 6 == 0:
    # if True:
        if not ((hour > 6) or (hour<2)):  # 2:00 ~ 6:00 休市
            db['stockDetails']['status'] = 'closed'
        else:
            db['stockDetails']['status'] = 'open'
        logging.debug("stock tick")
        if (db['stockDetails']['editCooldown']) > 0:  # if on rate limit cooldown (blocked by discord)
            db['stockDetails']['editCooldown'] -= 1  # cooldown is used to stop the bot from making requests
        else:
            sigma = 0.001
            startTime = time()
            for i in range(len(db['stockmarket'])):  # iterate every company
                logging.debug(f"iterate stock {i}")
                # gaussian distribution: avg = 0, stdev=5
                # 10^6 so we can make money from STONKS
                
                stockmarket = db['stockmarket'][i]
                stockmarket *= exp((10**(-6)) + sigma * gauss(mu=0, sigma=7)) # two sigmas are different
                db['stockmarket'][i] = stockmarket

                
                if i>= len(db['stockHistory']): 
                    db['stockHistory'].append(deque('')) # empty deque
                stockHistory_i = deque(db['stockHistory'][i])
                stockHistory_i.append(stockmarket) # add to history
                
                logging.debug(f"iterate stock {i} 2  len- {len(db['stockHistory'][i])}")
                
                while len(stockHistory_i) > 4320:  # queue max len 4320 -> 3d
                    stockHistory_i.popleft() # remove first item (like a queue)
                db['stockHistory'][i] = list(stockHistory_i)
                logging.debug(f"iterate stock {i} 3 len- {len(db['stockHistory'][i])}")
            
            # DELETE   
            # db['stockDetails']['editCooldown'] = 0
            # db['stockDetails']['status'] = 'open'
            logging.debug(f"stock finish refresh: {time()-startTime}")   
            # for stockEditNum in range(len(db['stockmarket'])):
        
            secretChannel = client.get_channel(secret_channel) 
            stockChannel = client.get_channel(1068514854207508480)  #發財樂透-股市 channel
            
            plotColor = '#e04646' if db['stockHistory'][stockEditNum][-1] < db['stockHistory'][stockEditNum][0] else '#5ce63c' # red if 
            plt.plot(db['stockHistory'][stockEditNum], color=plotColor)
            plt.savefig('files/fig.png')
            plt.clf()
            logging.debug("stock finish plot")
            file = discord.File('files/fig.png')
            if file:
                temp_message = await secretChannel.send("fig.png", file=file)
            else:
                file = discord.File('files/fig.png')
                temp_message = await secretChannel.send("fig.png", file=file)
            attachment = temp_message.attachments[0]
            
            embedColor = 0xe04646 if db['stockHistory'][stockEditNum][-1] < db['stockHistory'][stockEditNum][-2] else 0x5ce63c
            embed = discord.Embed(title = f"STOCKS {str(stockEditNum).zfill(4)} ({STARTUP_NAMES[stockEditNum][1]}) {STARTUP_NAMES[stockEditNum][0]}   {db['stockmarket'][stockEditNum]:.3f}", description = "",
                                  timestamp = datetime.datetime.utcnow(),
                                  color = embedColor)
            embed.set_image(url=attachment.url)
            # msg = await secretChannel.send(embed = embed)
            # print(msg)
            # print(type(msg))
            
            stockMessages = db['stockMessages']
            if stockEditNum < len(stockMessages):
                msg = await stockChannel.fetch_message(stockMessages[stockEditNum])
                try:
                    await msg.edit(embed=embed)
                    db['stockDetails']['status'] = 'open'
                    db['stockDetails']['editCooldown'] = 0
                except discord.errors.HTTPException:
                    print("\nBLOCKED\nTERMINATING NOW\n")
                    db['stockDetails']['status'] = 'closed'
                    db['stockDetails']['editCooldown'] = 90
                    os.system('kill 1')
                # print(f"successfully edited {i}")
            else:
                msg = await stockChannel.send(embed=embed)
                stockMessages.append(msg.id)
                db['stockMessages'] = stockMessages

            stockEditNum += 1
            stockEditNum %= len(db['stockmarket'])
            logging.debug("stock tick end")
            

@client.event
async def on_ready():  # after bot restart the bot is ready:
    print('Connected:', client.user)
    times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)  # 第 202300xx 期
    await client.change_presence(activity=discord.Game(name=f"第 {times} 期")) # Playing xxx
    subprocess.Popen(['python', 'loop.py'])
    #if not checkIfLotteryDraw.is_running(): checkIfLotteryDraw.start()  # remember to start da checking loop!!
    
    

@client.event
async def on_message(message):
    # global stockHistory
    if message.author == client.user:  # if send by bot itself then ignore
        return
    texts = message.content  # string
    rows = texts.split('\n')  # rows in message string (list)
    count = 0  # count how many rows has valid purchase
    db_guesses_ID = []  # lottery bought during this session (this message)
    invalidReason = ''
    for text in rows:  # iterate every row of message
        numbersMinusOne = len(re.findall(r'\d+[ ]+', text))
        # if user wants to buy a lottery
        # if in valid channel and has over (or equalto) 6 numbers 
        if int(message.channel.id) in channel_ids and numbersMinusOne >= 5: 
            bank = db['bank']  #  observedDict, stores everyone's money
            ID = str(message.author.id)
            if ID not in bank: # auto register
                register(ID)
            guess = [g.strip() for g in text.split(' ') if g != '']  # in case there is muitl space as seperator
            guess = sorted(list(map(int, guess)))  # the list of numbers users want to buy
            # if numbers in range of 1~42 and no duplicates
            if all([(g>0 and g<43) for g in guess]) and len(guess) == len(set(guess)):
                if db['bank'][ID] >= LOTTERY_COST: # purchase is valid
                    if len(guess) > 6: guess = guess[:6]  # if too many numbers, grab first 6
                    if ID not in db['guesses']: db['guesses'][ID] = []  # if it's first time to buy this 期
                    if len(db['guesses'][ID]) + len(db_guesses_ID) < 100: # if didnt buy THAT many during this 期
                        # ^ already bought         ^ buying right now
                        db_guesses_ID.append(guess) # record into database
                        count += 1 # count buy how many in ONE message
                    else:
                        invalidReason = 'buyTooMuch'
                        break
                else:
                    invalidReason = 'noMoney'
                    break
            else:
                invalidReason = 'wrongNumber'
                break
    # if any of the row is a valid purchase
    if count >= 1:
        # update database
        db['Quantity'] += count
        db['bank'][ID] -= (LOTTERY_COST * count)
        db['guesses'][ID].extend(db_guesses_ID)

        times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)  # "202300xx"
        await message.channel.send(
                    f"<@{ID}> 用 ${LOTTERY_COST*count} 買了第 {times} 期共 {count} 張。")
        await message.add_reaction('✅')
        
        await message.delete(delay=10)  # delete those numbers users sent after 10 seconds

        
        # write a csv file as detail/report/receipt and send it to user
        filepathname = f"files/receipt{ID[-3:]}{db['times']}.csv"
        with open(filepathname, 'w', newline='', encoding='utf8') as f:
            writer = csv.writer(f)
            header = ["No", "#1", "#2", "#3", "#4", "#5", "#6", "更多資訊"]
            writer.writerow(header)
            additionalInfo = [f"${LOTTERY_COST*count}", f"{count} 張", 
                              datetime.datetime.now().strftime("%Y/%m/%d"),
                              datetime.datetime.now().strftime("%H:%M:%S"),
                             "+0000", randint(1001,9999)]

            for n, row in enumerate(db_guesses_ID):
                row = [r.zfill(2) for r in map(str, row)]
                if n >= 6:
                    writer.writerow([str(n+1).zfill(2)] + row)
                else:  # first row (n=0), second row, third row...
                    writer.writerow([str(n+1).zfill(2)] + row + [additionalInfo[n]])
        await message.channel.send(file=discord.File(filepathname))
        try:
            os.remove(filepathname)
        except:
            pass

    # print why invalid? if it IS valid: invalidReason == '' > True
    if invalidReason == 'buyTooMuch':
        await message.channel.send(f"<@{ID}> 已經買太多了。")
    elif invalidReason == 'noMoney':
        await message.channel.send(f"<@{ID}> 的錢不夠。")
    elif invalidReason == 'wrongNumber':
        await message.channel.send(f"<@{ID}> 的購買不合法。")



    if int(message.channel.id) in channel_ids and texts.startswith('$'):
        command = texts[1:]
        ID = str(message.author.id)

        if command == "bank":
            if ID not in db['bank']: register(ID)
            await message.reply(
            f"<@{ID}> 共有 ${db['bank'][ID]}")

        elif command == "purchases" or command == 'pur':
            times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)
            if ID in db['guesses']:
                # await message.reply()
                if len(db['guesses'][ID]) > 10:
                    toPrint = db['guesses'][ID][:10]
                    toPrint = map(str, list(map(list,toPrint)))
                    await message.reply(f"<@{ID}> 於第 {times} 期共買了 {len(db['guesses'][ID])} 張：\n" + '\n'.join(toPrint)+'\n...等等等')
                else: 
                    toPrint = db['guesses'][ID]
                    toPrint = map(str, list(map(list,toPrint)))
                    await message.reply(f"<@{ID}> 於第 {times} 期共買了 {len(db['guesses'][ID])} 張：\n" + '\n'.join(toPrint))
            else:
                await message.reply(f"<@{ID}> 尚未於第 {times} 期購買。")

        elif command == "daily":
            logging.debug('dailied')
            if ID not in db['daily']:
                db['daily'].append(ID)
                if ID not in db['bank']: register(ID)
                db['bank'][ID] += DAILY_INCOME
                await message.reply(f"<@{ID}> 領取了每日收入 ${DAILY_INCOME}。")
            else:
                await message.reply(f"<@{ID}> 今日已領取過每日收入。")



                    # for elio (刑法 bruh) and alexhou (just in case)
        elif command.startswith("fine"):
            if ID == "843393747545751562" or ID == "693091131168260137":
                fineID, fine = command.split(' ', 2)[1:]
                if ' ' in fine: fine, reason = fine.split(' ', 1)
                fineID = fineID.strip("<@>")
                # print(id)
                await message.channel.send(
                    f"<@{fineID}> 被處以罰金 ${fine}，理由：{reason}")
                db['bank'][fineID] -= int(fine)



        # stock related commands begin
        elif command == 'stockbank' or command == 'purchases stock' or command == 'pur stock':
            if ID not in db['stockbank']: db['stockbank'][ID] = Counter()
            if len(db['stockbank'][ID]) > 0:
                sortedBank = sorted(db['stockbank'][ID].items(), key=lambda v: int(v[0]))
                # sortedBank
                toPrint = '\n'.join([f"`{str(k).zfill(4)}` ({STARTUP_NAMES[int(k)][1]}) {STARTUP_NAMES[int(k)][0]}    {v} 張" for k, v in sortedBank if v != 0])
                await message.reply(
                        f"<@{ID}> 的股票有：\n{toPrint}。")
            else:
                await message.reply(f"<@{ID}> 目前沒有股票。")
                
        
        elif (db['stockDetails']['status'] == 'open'):
            if command == ("stockmarket"):
                toPrint = [f"{str(n).zfill(4)}   { ('(' + p[1][1] + ') ').ljust(7) + p[1][0].ljust(29)}  {round(p[0], 3):.3f}" for n, p in enumerate(zip(db['stockmarket'], STARTUP_NAMES))]
                await message.reply("股市如下：\n```"+'\n'.join(toPrint)+'\n```', delete_after=60)
    
            elif command.startswith("buystock"):
                stockNum = int(command.split(' ', 1)[1])
                logging.debug(stockNum)
                sharePrice = round(db['stockmarket'][stockNum] * 1000)
                if db['bank'][ID] >= sharePrice:
                    logging.debug("price", sharePrice)
                    db['bank'][ID] -= sharePrice
                    if ID not in db['stockbank']: db['stockbank'][ID] = Counter()
                    tmpCounter = Counter(db['stockbank'][ID])
                    tmpCounter.update({str(stockNum): 1})
                    db['stockbank'][ID] = tmpCounter
                    await message.reply(
                        f"<@{ID}> 花了 ${sharePrice} 買一張股票，股票編號：{str(stockNum).zfill(4)}")
                else:
                    await message.reply(
                        f"<@{ID}> 的錢不夠。")
    
            elif command.startswith("sellstock"):
                stockNum = int(command.split(' ', 1)[1])
                print(stockNum)
                sharePrice = round(db['stockmarket'][stockNum] * 1000)
                print("price", sharePrice)
                if db['stockbank'][ID][str(stockNum)] > 0:
                    db['bank'][ID] += sharePrice
                    db['bank'][ID] = int(db['bank'][ID])
                    tmpCounter = Counter(db['stockbank'][ID])
                    tmpCounter.subtract(Counter({str(stockNum): 1}))
                    db['stockbank'][ID] = tmpCounter
                    await message.reply(
                        f"<@{ID}> 以 ${sharePrice} 的價格賣了一張股票，股票編號：{str(stockNum).zfill(4)}")
                else:
                    await message.reply(
                        f"<@{ID}> 股票編號 {str(stockNum).zfill(4)} 的股票不夠。")
    
            elif command.startswith('stockchart'):
                stockNum = command.split(' ', 1)[1]
                
                if ' ' in stockNum: 
                    stockNum, duration = map(int, stockNum.split(' ', 1)) # duration specified
                    plotColor = '#e04646' if db['stockHistory'][stockNum][-1] < db['stockHistory'][stockNum][0] else '#5ce63c'
                    if len(db['stockHistory'][stockNum]) > duration:
                        plotColor = '#e04646' if db['stockHistory'][stockNum][-1] < db['stockHistory'][stockNum][0-duration] else '#5ce63c'
                        plt.plot(db['stockHistory'][stockNum][0-duration:], color=plotColor)
                    else:
                        plt.plot(db['stockHistory'][stockNum], color=plotColor)
                else: 
                    stockNum = int(stockNum)  # duration not specified
                    plotColor = '#e04646' if db['stockHistory'][stockNum][-1] < db['stockHistory'][stockNum][0] else '#5ce63c'
                    if len(db['stockHistory'][stockNum]) > 300:
                        plotColor = '#e04646' if db['stockHistory'][stockNum][-1] < db['stockHistory'][stockNum][-300] else '#5ce63c'
                        plt.plot(db['stockHistory'][stockNum][-300:], color=plotColor)
                    else:
                        plt.plot(db['stockHistory'][stockNum], color=plotColor)
                
                plt.savefig('files/fig.png')
                plt.clf()
                await message.reply(file=discord.File('files/fig.png'), delete_after=20)
            # stock related commands end
        elif 'stock' in command:
            await message.reply("股市休市中...")
    


try:
    keep_alive.keep_alive()
    client.run(token)
except discord.errors.HTTPException:
    print("\n\n\nBLOCKED BY RATE LIMITS\nTERMINATING NOW\n\n\n")
    os.system('kill 1')