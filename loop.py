from replit import db
import discord
client = discord.Client()

import datetime
from random import sample, gauss
from time import time
from collections import deque
import os

from discord.ext import tasks
from math import log, ceil, exp  # log() = log_e() = ln()
from math import e as math_e
import matplotlib.pyplot as plt

# import sys
prizeTable = [0, 2, 6, 10, 600, 60000, 10000000]
import openpyxl
import logging
print("hello world")
stockEditNum = 0
for name, logger in logging.root.manager.loggerDict.items():
    logger.disabled=True
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.DEBUG)
tradeStockCount = 4
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

test_channel = 882982896934219817  # LANG-test
secret_channel = 1068798588622225418  # fig.png channel
GUESS_channel = 1067835837397618758  # main channel (in GUESS?)
geo_channel = 968951342456537138  # bot-commands
channel_ids = (test_channel, GUESS_channel, geo_channel)


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
async def on_ready(): 
    
#if not checkIfLotteryDraw.is_running(): 
    checkIfLotteryDraw.start()  # remember to start da checking loop!!
token = os.environ['DISCORD_BOT_SECRET']
client.run(token)
