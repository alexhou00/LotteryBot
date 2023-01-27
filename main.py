import discord
client = discord.Client()

import datetime
from random import sample, gauss
from collections import Counter
import os
import re
from discord.ext import tasks
from math import log, ceil, exp  # log() = log_e() = ln()
from math import e as math_e
import matplotlib.pyplot as plt
import csv

import keep_alive

# import pandas as pd
# import pdfkit
import openpyxl

from replit import db

# to do: $buy (quick pick), one xlsx, receipt csv[done], self edit stonks, pm, ling2gu3, 數值自動監控 and notif,
#         reply users instead of tags, stock permanent history, 收盤
# future to do: BLACKJACK


token = os.environ['DISCORD_BOT_SECRET']

test_channel = 882982896934219817  # LANG-test
GUESS_channel = 1067835837397618758  # main channel (in GUESS?)
geo_channel = 968951342456537138  # bot-commands
channel_ids = (test_channel, GUESS_channel, geo_channel)

LOTTERY_COST = 2
DAILY_INCOME = 100

tradeStockCount = 0  # count loop to check if time to trade stock (every 6 loops currently)

# also another prizeTable in tasks.loop if this one here is edited
prizeTable = [0, 2, 6, 10, 600, 60000, 10000000]
KEYPAD_TABLE = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣','8️⃣','9️⃣')
stockHistory = [[] for i in db['stockmarket']]  # len stockHistory = len db['stockmarket']

print(db.keys())

## DELETE THINGS HERE 
##
##

def register(ID):  # user auto register / join the bank system
    db['bank'][ID] = 100
    db['guesses'][ID] = list()

@tasks.loop(seconds=10)  # repeat after every 10 seconds
async def checkIfLotteryDraw():  # just loop idc the names
    global tradeStockCount, prizeTable, stockHistory
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
            
            await channel.send(f"本期所有人共買了 {q} 張，因此對中三個以上的獎金將個別乘上 {log(q/x+1)} 並無條件進位至整數，而獎金陣列 P = {prizeTable[1:]}，買氣越旺獎金越高！")
        for person, guesses in db['guesses'].items():  # for person in all guesses (Person==ID, type:str)
            countList = []  # deprecated in my code: count 對中幾個 each guess and store each guess (row) here
            countSum = 0  # prize sum
            csvList = []  # list to create csv (deprecated??)
            for n, guess in enumerate(guesses):  # for each guess of a person in that person's guesses
                count = sum(number in results for number in guess)  # count how many True's
                db['bank'][person] += prizeTable[count]
                countList.append(count)
                csvList.append([n+1] + list(guess) + [count])
                countSum += prizeTable[count]  # add to prize sum
            if len(guesses) == 1:  # if this person only purchased one lottery
                await channel.send(f"<@{person}> 對中了 {count} 個數字並贏得了 ${prizeTable[count]}，現在他有 ${db['bank'][person]}。")
            else:   # he/she purchased more than one lottery
                # await channel.send(f"<@{person}> 各對中了 {countList} 個數字並總共贏得了 ${countSum}，現在他有 ${db['bank'][person]}。")
                await channel.send(f"<@{person}> 總共贏得了 ${countSum}，詳細結果請見附檔，現在他有 ${db['bank'][person]}。")
                wb = openpyxl.Workbook()  # excel file (wb: workbook == file)
                ws = wb.active  # current WorkSheet (default named Sheet)
                with open('files/report.csv', 'w', newline='', encoding='utf8') as f:
                    writer = csv.writer(f)  # csv writer object
                    # write header row
                    header = ["序號", "#1", "#2", "#3", "#4", "#5", "#6", "對中數目"]
                    writer.writerow(header)
                    ws.append(header)
                    for row in csvList:
                        writer.writerow(row)
                        ws.append(row)
                wb.save('files/report.xlsx')
                await channel.send(file=discord.File('files/report.xlsx'))
                os.remove('files/report.csv')

        db['guesses'] = {}
        await channel.send(f"以上就是本期的開獎！") 

    # STONKS REFRESH
    if tradeStockCount % 6 == 0:
    # if True:
        print("stock tick")
        sigma = 0.001
        for i in range(len(db['stockmarket'])):  # iterate every company
            # gaussian distribution: avg = 0, stdev=5
            # 10^6 so we can make money from STONKS
            db['stockmarket'][i] *= exp((10**(-6)) + sigma * gauss(mu=0, sigma=5)) # two sigmas are different
            stockHistory[i].append(db['stockmarket'][i])
            

@client.event
async def on_ready():  # after bot restart the bot is ready:
    print('Connected:', client.user)
    times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)  # 第 202300xx 期
    await client.change_presence(activity=discord.Game(name=f"第 {times} 期")) # Playing xxx
    checkIfLotteryDraw.start()  # remember to start da checking loop!!
    
    # stonks channel: edit and update stonk info
    '''stockChannel = client.get_channel(1068514854207508480)  #發財樂透-股市 channel
    chart = discord.File('files/fig.png')
    embed = discord.Embed(title = "股票 0000", description = "",
                      timestamp = datetime.utcnow(),
                      color = 0x26ad00)
     embed.set_image(
   url="attachment://files/fig.png"
)'''
    

@client.event
async def on_message(message):
    global stockHistory
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
        times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)  # "202300xx"
        await message.channel.send(
                    f"<@{ID}> 用 ${LOTTERY_COST*count} 買了第 {times} 期共 {count} 張。")
        await message.add_reaction('✅')
        
        await message.delete(delay=10)  # delete those numbers users sent after 10 seconds

        # update database
        db['Quantity'] += count
        db['bank'][ID] -= (LOTTERY_COST * count)
        db['guesses'][ID].extend(db_guesses_ID)

        # write a csv file as detail/report/receipt and send it to user
        filepathname = f"files/receipt{ID[-3:]}{db['times']}.csv"
        with open(filepathname, 'w', newline='', encoding='utf8') as f:
            writer = csv.writer(f)
            header = ["序號", "#1", "#2", "#3", "#4", "#5", "#6", "更多資訊"]
            writer.writerow(header)
            additionalInfo = [f"${LOTTERY_COST*count}", f"{count} 張", 
                              datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S +0000")]

            for n, row in enumerate(db_guesses_ID):
                if n >= 3:
                    writer.writerow([n+1] + row)
                else:  # first row (n=0), second row, third row...
                    writer.writerow([n+1] + row + [additionalInfo[n]])
        await message.channel.send(file=discord.File(filepathname))
        os.remove(filepathname)

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
            await message.channel.send(
            f"<@{ID}> 共有 ${db['bank'][ID]}")

        elif command == "purchases":
            times = str(datetime.datetime.today().year) + str(db['times']).zfill(4)
            if ID in db['guesses']:
                await message.channel.send(f"<@{ID}> 於第 {times} 期共買了 {len(db['guesses'][ID])} 張：")
                if len(db['guesses'][ID]) > 10:
                    toPrint = db['guesses'][ID][:10]
                    toPrint = map(str, list(map(list,toPrint)))
                    await message.channel.send('\n'.join(toPrint)+'\n...等等等')
                else: 
                    toPrint = db['guesses'][ID]
                    toPrint = map(str, list(map(list,toPrint)))
                    await message.channel.send('\n'.join(toPrint))
            else:
                await message.channel.send(f"<@{ID}> 尚未於第 {times} 期購買。")

        elif command == "daily":
            if ID not in db['daily']:
                db['daily'].append(ID)
                if ID not in db['bank']: register(ID)
                db['bank'][ID] += DAILY_INCOME
                await message.channel.send(f"<@{ID}> 領取了每日收入 ${DAILY_INCOME}。")
            else:
                await message.channel.send(f"<@{ID}> 今日已領取過每日收入。")

        # stock related commands begin
        elif command == ("stockmarket"):
            toPrint = [f"{str(n).zfill(4)}  {round(p, 3):.3f}" for n, p in enumerate(db['stockmarket'])]
            await message.channel.send("股市如下：\n```"+'\n'.join(toPrint)+'\n```', delete_after=20)

        elif command.startswith("buystock"):
            stockNum = int(command.split(' ', 1)[1])
            print(stockNum)
            sharePrice = round(db['stockmarket'][stockNum] * 1000)
            if db['bank'][ID] >= sharePrice:
                print("price", sharePrice)
                db['bank'][ID] -= sharePrice
                if ID not in db['stockbank']: db['stockbank'][ID] = Counter()
                tmpCounter = Counter(db['stockbank'][ID])
                tmpCounter.update({str(stockNum): 1})
                db['stockbank'][ID] = tmpCounter
                await message.channel.send(
                    f"<@{ID}> 花了 ${sharePrice} 買一張股票，股票編號：{str(stockNum).zfill(4)}")
            else:
                await message.channel.send(
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
                await message.channel.send(
                    f"<@{ID}> 以 ${sharePrice} 的價格賣了一張股票，股票編號：{str(stockNum).zfill(4)}")
            else:
                await message.channel.send(
                    f"<@{ID}> 股票編號 {str(stockNum).zfill(4)} 的股票不夠。")

        elif command == 'stockbank':
            if ID not in db['stockbank']: db['stockbank'][ID] = Counter()
            if len(db['stockbank'][ID]) > 0:
                toPrint = '\n'.join([f"`{str(k).zfill(4)}`  `{v}`張" for k,v in sorted(db['stockbank'][ID].items()) if v!=0])
                await message.channel.send(
                        f"<@{ID}> 的股票有：\n{toPrint}。")
            else:
                await message.channel.send(f"<@{ID}> 目前沒有股票。")

        elif command.startswith('stockchart'):
            stockNum = int(command.split(' ', 1)[1])
            plt.plot(stockHistory[stockNum])
            plt.savefig('files/fig.png')
            plt.clf()
            await message.channel.send(file=discord.File('files/fig.png'), delete_after=20)
        # stock related commands end

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
        else:
            await message.channel.send("未知的指令")

try:
    keep_alive.keep_alive()
    client.run(token)
except discord.errors.HTTPException:
    print("\n\n\nBLOCKED BY RATE LIMITS\nTERMINATING NOW\n\n\n")
    os.system('kill 1')