import config
import vk_api
import telebot
import re
import time
import threading
import requests
import random
from datetime import datetime
from tqdm import tqdm
from peewee import *
from Models.handlers import *
from Models.User import *
from Models.repository import *
vk=vk_api.VkApi(token=config.vktoken)
bot=telebot.TeleBot(config.tlgtoken)

PATTERN=r'^t.me\/[a-zA-Z0-9]*'
CD=5

def write_vk_ms(user_id, s):
    vk.method('messages.send', {'user_id':user_id,'message':s})


def try_auth_user(uid,*urls): #later
    for url in urls:
            this_user,err=auth_user(uid,url)
            if (this_user):
                if (this_user.vkid and this_user.tname and this_user.chatid):
                    return this_user
            else:
                print(err)
    return None

def auth_user(uid,url):
    check=find_user_by_vk(uid)
    if(check):
        if (check.vkid and check.tname and check.chatid):
            return check, 'ok'
    if (re.fullmatch(PATTERN, url)):
        tname=url[5:].lower()
        this_user=find_user_by_tg(tname)
        if (not this_user): #1
            this_user=User(vkid=uid,tname=tname,chatid=None)
            this_user.save()
            return None, "для завершения регистрации перейдите по ссылке t.me/LetterFromVkBot и введите /start"
        elif (not this_user.chatid): #значит уже прошел #1
           return None, "для завершения регистрации перейдите по ссылке t.me/LetterFromVkBot и введите /start \n без этого я не смогу работать с вами"
        elif (not this_user.vkid): #значит пользователь регистрировался в телеге
            this_user.vkid=uid
            this_user.save()
            return this_user, 'ok' #вот тут я не уверен, нужно ли возвращать его
    else:
        return None, "ссылка не прошла regex"
    


@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    check=find_user_by_tg(m.chat.username.lower())
    if(check):
        if (check.chatid):
            bot.send_message(cid, "I already know you, no need for me to scan you again!")
        else:
            check.chatid=cid
            check.save()
            bot.send_message(cid, "Hello, stranger, let me scan you...")
            bot.send_message(cid, "Scanning complete, I know you now")
    else:
        check=User(tname=m.chat.username.lower(),chatid=cid)
        check.save()
        
operations ={
    'photo': lambda att,user: handle_photo(att,user,b=bot),
    'audio': lambda att,user: handle_audio(att,user,b=bot),
    'video': lambda att,user: handle_video(att,user,b=bot),
    'doc': lambda att,user: handle_doc(att,user,b=bot),
    'link': lambda att,user: handle_link(att,user,b=bot),
}

def main():
    cooldown=CD
    threading.Thread(target=lambda:bot.polling(none_stop=True),daemon=True).start()
    while True:
        msgs = vk.method('messages.get', {'out': 0,'count': 100,'time_offset': cooldown})
        starttime = time.time()
        for item in msgs['items']:
            #Для каждого сообщения
            vk_id=item['user_id']
            msg_body=item['body']
            
            this_user,err = auth_user(vk_id,msg_body)
            if (not this_user):
                write_vk_ms(vk_id,err)
                continue

            #все ОК!! направляем
            if(msg_body):
                bot.send_message(this_user.chatid,msg_body)
                print('sended')
            
            #TODO reposts, forwarded messages
            if ( 'attachments' in item):
                for att in item['attachments']:
                    type = att['type']
                    response = operations[type](att[type],this_user)
                    if (response):
                        print('gotcha, send 1 attachment')
                    else:
                        print('something went wrong')
                        
            if ('geo' in item):
                coor=item['geo']['coordinates'].split(' ')
                bot.send_location(this_user.chatid,coor[0],coor[1])
        #end items

        endtime=time.time()-starttime
        if(endtime < cooldown):
            if (cooldown != CD):
                cooldown=CD
            print('sleeeeep ',cooldown,' sec')
            time.sleep(cooldown)
        else:
            cooldown=int(endtime)
    #end while
#end main
    
   

if __name__ == "__main__":
    main()