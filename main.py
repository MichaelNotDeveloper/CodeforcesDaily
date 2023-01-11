from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import io
import time as t
from utils import settings
from utils import rater

plt.switch_backend('Agg')

import telebot
import PIL
from PIL import Image
from requests import get
import pandas as pd
from pathlib import Path
from telebot import types

def getnum(filename):
    file = open(filename, 'r+')
    num = int(file.readline().strip().split(',')[0])
    file.close()
    return num

def delnum(filename):
    file = open(filename, 'r+')
    txt = file.readline().strip()
    num = txt.split(',')[0]
    file.close()
    file = open(filename, 'r+')
    file.write(txt[len(num)+1:]+' '*10)
    file.close()

def writenum(filename, num):
    file = open(filename, 'r+')
    txt = file.readline().strip()
    file.close()
    file = open(filename, 'r+')
    file.write(txt+str(num)+',')
    file.close()


#
admins = settings.admins
dataname = settings.dataname
contest_data_name = settings.contest_data_name
token = settings.token
today_contest = getnum(contest_data_name)
delay_registration_time_sec = 2*60
#

#
def connect_to_database():
    my_file = Path(dataname)
    
    df = pd.DataFrame()
    
    if my_file.is_file():
        df = pd.read_csv(dataname)
    else:
        df = pd.DataFrame({"cfid":["@Grandmaster_gang"], "tgid":[602327086], "score":[1500], "hist": '0;', "points": '0;', "Change" : 0})
        df.to_csv(dataname, index=False)
    df = df.sort_values('score', ascending=False)
    return df
    
df = connect_to_database()
print(df)
#

#
bot = telebot.TeleBot(token)
log_queue = dict()
#

rank_model = rater.Ranker()

#
def usual_markup():

    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('🧭 Rang')
    itembtn2 = types.KeyboardButton('📊 Top')
    itembtn3 = types.KeyboardButton('📊 Rang History')
    itembtn4 = types.KeyboardButton('📊 Contest History')
    itembtn5 = types.KeyboardButton('🎉 Current Contest')
    itembtn6 = types.KeyboardButton('🧮 Calculate my Results now')
    
    markup.add(itembtn1, itembtn2)
    markup.add(itembtn3, itembtn4)
    markup.add(itembtn5, itembtn6)

    return markup
#

def update():
    global df
    df = df.sort_values('score', ascending=False)
    df.to_csv(dataname, index=False)

#


#
@bot.message_handler(commands=['start'])
def start_message(message):
    print(message.chat.id, "strt")
    bot.send_message(message.chat.id, '🍀 Hello, I am a system what allows users to participate in Codeforces rounds daily!\n\n🍀 To register send me your Codeforces account with /register mark\n\nExample : /register tourist')
#
    
#
@bot.message_handler(commands=['register'])
def add_to_database(message):
    global df
    if (len(message.text.split()) != 2):
        bot.send_message(message.chat.id, '🫠 Something wrong!\nPlease, follow the format')
        return
    bot.send_message(message.chat.id, f'⭐ Nice! ⭐ \nTo proof what it is really you, try to get Compilation Error status on this task : https://codeforces.com/problemsets/acmsguru/problem/99999/453 \n\n After that, send me a /complete mark. \n\nCareful! You only have {delay_registration_time_sec//60} mins!\n')
    print(message.chat.id, "add")
    log_queue[message.chat.id] = message.text.split()[1]
#
    
#
@bot.message_handler(commands=['complete'])
def add_to_database(message):
    global df
    good = 0
    if message.chat.id in log_queue:
        probs = get(f'https://codeforces.com/api/problemset.recentStatus?problemsetName=acmsguru&count=10').json()['result']
        print(log_queue[message.chat.id])
        for prob in probs:
            if (prob['problem']['index'] == '453' and prob['verdict'] == 'COMPILATION_ERROR' and prob['author']['members'][0]['handle'] == log_queue[message.chat.id] and t.time()-prob['creationTimeSeconds'] <= delay_registration_time_sec):
                good = 1
                break
    
    if not good:
        bot.send_message(message.chat.id, "🛌 Sorry pal, but it seems like your submission is too late!")
        return
    
    bot.send_message(message.chat.id, "🚀 Congratulations! You're all set!", reply_markup = usual_markup())
    rankhist = list()
    delhist = list()
    
    contsts = get(f'https://codeforces.com/api/user.rating?handle={log_queue[message.chat.id]}').json()['result']
    
    for cntst in contsts:
        rankhist.append(int(cntst['newRating']))
    
    for i in range(len(rankhist) - 1):
        delhist.append(rankhist[i + 1] - rankhist[i])
    
    user = message.chat.id
    name = log_queue[message.chat.id]
    
    rhist = ""
    dhist = ""
    
    for x in rankhist:
        rhist += str(x) + ';'
    
    for x in delhist:
        dhist += str(x) + ';'
    if (len(df[df["tgid"] == user]) == 0) :
        df = df.append(pd.DataFrame({"cfid":[name], "tgid":[user], "score":[rankhist[-1]], "hist": rhist, "points": dhist, "Change" : 0}))
    else:
        df.loc[df['tgid'] == user] = pd.DataFrame({"cfid":[name], "tgid":[user], "score":[rankhist[-1]], "hist": rhist, "points": dhist, "Change" : 0})
    update()
#
    
#
@bot.message_handler(func=lambda x: x.text == '🧭 Rang')
def my_rating(message):
    print(message.chat.id, "rng")
    user = message.chat.id
    
    if (len(df[df["tgid"] == message.chat.id]) == 0):
        bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
        return
    
    bot.send_message(message.chat.id, f'🗻 Your rating is : {int(df[df["tgid"] == user]["score"])}, not bad!', reply_markup = usual_markup())
    
        
#
        
#
@bot.message_handler(func=lambda x: x.text == '📊 Top')
def ratings(message):
    if (len(df[df["tgid"] == message.chat.id]) == 0):
        bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
        return

    print(message.chat.id, "rt")
    output = ""
    indx = 0
    TOPCOUNT = 10
    medals = ['🌕', '🌖', '🌗', '🌘', '🌑']
    for row in df[["cfid", "score"]].iterrows():
        type = medals[min(len(medals)-1, indx)]
        output += f"{type} {row[1]['cfid'][:]} : {row[1]['score']} \n"
        indx += 1
        if indx == TOPCOUNT:
            break
    bot.send_message(message.chat.id, "⬆️ Top Codepowers users :\n" + output, reply_markup = usual_markup())
#

#
@bot.message_handler(func=lambda x: x.text == '🎉 Current Contest')
def cntst(message):
    if (len(df[df["tgid"] == message.chat.id]) == 0):
        bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
        return
    
    print(message.chat.id, "cntst")
    bot.send_message(message.chat.id, f"💌 Today's contest : {'https://codeforces.com/contest/'+str(today_contest)}")
        
#

#
@bot.message_handler(func=lambda x: x.text == '📊 Rang History')
def cntst(message):
    if (len(df[df["tgid"] == message.chat.id]) == 0):
        bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
        return

    print(message.chat.id, "rang_history")
    
    data =  list(map(int, str(df[df["tgid"] == message.chat.id]["hist"][0]).split(';')[:-1]))
    fig, ax = plt.subplots()

    canvas = FigureCanvas(fig)
    canvas.draw()

    ax.plot(data, c = 'black' , marker = '.')
    ax.grid()
    ax.margins(0)
    
    if (np.min(data) <= 1200):
        ax.axhspan(np.min(data), 1200, facecolor=(.8, .8, .8), alpha=1)
    ax.axhspan(1200, 1400, facecolor=(155/255, 252/255, 135/255), alpha=1)
    ax.axhspan(1400, 1600, facecolor=(144/255, 218/255, 189/255), alpha=1)
    ax.axhspan(1600, 1900, facecolor=(117/255, 170/255, 249/255), alpha=1)
    ax.axhspan(1900, 2100, facecolor=(239/255, 142/255, 249/255), alpha=1)
    ax.axhspan(2100, 2300, facecolor=(247/255, 206/255, 145/255), alpha=1)
    ax.axhspan(2300, 2400, facecolor=(245/255, 190/255, 103/255), alpha=1)
    ax.axhspan(2300, 2400, facecolor=(238/255, 127/255, 123/255), alpha=1)

    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=300)
    img = Image.open(img_buf)
        
    bot.send_photo(message.chat.id, img)
    img_buf.close()
#

#
@bot.message_handler(func=lambda x: x.text == '📊 Contest History')
def cntst(message):
    if (len(df[df["tgid"] == message.chat.id]) == 0):
        bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
        return

    print(message.chat.id, "contest_history")
    
    print(str(df[df["tgid"] == message.chat.id]["points"][0]).split(';')[:-1])
    data =  list(map(int, str(df[df["tgid"] == message.chat.id]["points"][0]).split(';')[:-1]))
    
    fig, ax = plt.subplots()

    canvas = FigureCanvas(fig)
    canvas.draw()

    ax.plot(data, c = 'black' , marker = '.')
    ax.grid()
    ax.margins(0)
    
    if (np.min(data) < -50):
        ax.axhspan(np.min(data), -50, facecolor=(238/255, 127/255, 123/255), alpha=1)
    
    ax.axhspan(-50, 0, facecolor=(245/255, 190/255, 103/255), alpha=1)
    ax.axhspan(0, 50, facecolor=(155/255, 252/255, 135/255), alpha=1)
    
    if (np.max(data) > 50):
        ax.axhspan(50, np.max(data), facecolor=(144/255, 218/255, 189/255), alpha=1)
    
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', dpi=300)
    img = Image.open(img_buf)
        
    bot.send_photo(message.chat.id, img)
    img_buf.close()
    
#


            
#
@bot.message_handler(commands=['end'])
def end_contest(message):
        global df
        
        if message != None:
            if (not (message.chat.id in admins)):
                print("Hacking attempt")
                return
        
        for row in df.iterrows():
            user = row[1]['cfid']
            print(user)
            data = get(f'https://codeforces.com/api/contest.standings?contestId={today_contest}&showUnofficial=true&handles={user}').json()['result']['rows']
            if (not len(data)) or int(df.loc[df['tgid'] == row[1]['tgid'], "Change"]) :
                bot.send_message(str(row[1]['tgid']), f"Contest is ending and we are calculating results! 🍾\nRating is about to be changed!!! 🎁")
            else :
                print(row[1]['cfid'])
                rank = row[1]['score']
                points = data[0]['points']
                penalty = data[0]['penalty']
                
                cfdata = rank_model.getrank(today_contest, points, rank, penalty)
                
                df.loc[df['tgid'] == row[1]['tgid'], "score"] = int(df.loc[df['tgid'] == row[1]['tgid'], "score"])+int(cfdata[0])
                df.loc[df['tgid'] == row[1]['tgid'], "hist"] = df.loc[df['tgid'] == row[1]['tgid'], "hist"].apply(lambda x:x + str(int(df.loc[df['tgid'] == row[1]['tgid'], "score"])) + ';')
                df.loc[df['tgid'] == row[1]['tgid'], "points"] = df.loc[df['tgid'] == row[1]['tgid'], "points"].apply(lambda x:x + str(cfdata[0]) + ';')
                df.loc[df['tgid'] == row[1]['tgid'], "Change"] = 1
                
                
                bot.send_message(str(row[1]['tgid']), f"Contest is ending and we are calculating results! 🍾\nRating is about to be changed!!! 🎁")
                bot.send_message(str(row[1]['tgid']), f"✅ Rating change is : {cfdata[0]}\n✅ Virtual poistion is : {cfdata[2]}\n✅ Expected rank is : {cfdata[1]}")
                
                update()
        
        delnum(contest_data_name)
        today_contest = getnum(contest_data_name)
        
        for row in df[["tgid"]].iterrows():
            bot.send_message(str(row[1]['tgid']), f"Контест на сегодня : {'https://codeforces.com/contest/'+str(today_contest)}")
            
        for row in df.iterrows():
            f.loc[df['tgid'] == row[1]['tgid'], "Change"] = 0
#



#
@bot.message_handler(commands=['state'])
def add_contest(message):
        global today_contest
        
        if (not (message.chat.id in admins)):
            print("Hacking attempt")
            return
    
        if (not (message.chat.id in admins)):
            print("Hacking attempt")
            return
            
        writenum(contest_data_name, message.text.split()[1])
#



#
@bot.message_handler(func=lambda x: x.text == '🧮 Calculate my Results now')
def change_rate(message):
        global df
        
        if (len(df[df["tgid"] == message.chat.id]) == 0):
            bot.send_message(message.chat.id, "Sorry, I can't see you logged in!")
            return
        
        user = (df[df["tgid"] == message.chat.id]["cfid"][0])

        data = get(f'https://codeforces.com/api/contest.standings?contestId={today_contest}&showUnofficial=true&handles={user}').json()['result']['rows']
        if (not len(data)) or int(df.loc[df['tgid'] == message.chat.id, "Change"]) :
            bot.send_message(message.chat.id, f"Sorry but, you can't do it right now!")
        else :
            
            rank = int(df.loc[df['tgid'] == message.chat.id, 'score'])
            points = data[0]['points']
            penalty = data[0]['penalty']
            
            cfdata = rank_model.getrank(today_contest, points, rank, penalty)
            
            df.loc[df['tgid'] == message.chat.id, "score"] = int(df.loc[df['tgid'] == message.chat.id, "score"])+int(cfdata[0])
            df.loc[df['tgid'] == message.chat.id, "hist"] = df.loc[df['tgid'] == message.chat.id, "hist"].apply(lambda x:x + str(int(df.loc[df['tgid'] == message.chat.id, "score"])) + ';')
            df.loc[df['tgid'] == message.chat.id, "points"] = df.loc[df['tgid'] == message.chat.id, "points"].apply(lambda x:x + str(cfdata[0]) + ';')
            df.loc[df['tgid'] == message.chat.id, "Change"] = 1
            
            bot.send_message(message.chat.id, f"✅ Rating change is : {cfdata[0]}\n✅ Virtual poistion is : {cfdata[2]}\n✅ Expected rank is : {cfdata[1]}")
            
            update()
#


if __name__ == "__main__":
    bot.polling(none_stop=True)
