import config
import vk_api
import telebot
import re
import time
import threading
import requests
import random
from tqdm import tqdm
from peewee import *
from Models.User import User


vk=vk_api.VkApi(token=config.vktoken)
bot=telebot.TeleBot(config.tlgtoken)


COOLDOWN=5
PATTERN=r'^t.me\/[a-zA-Z0-9]*'
VALUES = {'out': 0,'count': 100,'time_offset': COOLDOWN}

def write_vk_ms(user_id, s):
    vk.method('messages.send', {'user_id':user_id,'message':s})

def find_user_by_vk(uid):
    try:
        return User.select().distinct().where(User.vkid==uid).get()
    except:
        return None
    
def find_user_by_tg(tname):
    try:
        return User.select().distinct().where(User.tname==tname).get()
    except:
        return None

def try_auth_user(uid,*urls):
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
        

def telegrambot():
    bot.polling(none_stop=True)


def main():
    threading.Thread(target=telegrambot,daemon=True).start()
    while True:
        msgs= vk.method('messages.get', VALUES)
        for item in msgs['items']:
            #Для каждого сообщения
            vk_id=item['user_id']
            msg_body=item['body']
            
            this_user,err = auth_user(vkid,msg_body)
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
                    print(att['type'])

                    if(att['type']=='photo'):
                        attphoto=att['photo']
                        max=int(0)
                        for ph in attphoto:
                            if(re.fullmatch(r'^photo_[0-9]*',ph)):
                                if(int(ph[6:])>max):
                                    max=int(ph[6:])
                        print(max)
                        bot.send_photo(this_user.chatid,attphoto['photo_'+str(max)])

                    elif(att['type']=='audio'):
                        if (att['audio']['url']):
                            bot.send_audio(this_user.chatid,att['audio']['url'])
                            write_vk_ms(vk_id,'отправлено')
                        else:
                            print('нету url')

                    elif(att['type']=='video'):
                        print('video')

                    elif(att['type']=='doc'):
                        print('doc')
                        
                    elif(att['type']=='link'):
                        print('link')
                        bot.send_message(this_user.chatid,att['link']['url'])
            if ('geo' in item):
                coor=item['geo']['coordinates'].split(' ')
                bot.send_location(this_user.chatid,coor[0],coor[1])
        #end items
        print('sleeeeep ',COOLDOWN,' sec')
        time.sleep(COOLDOWN)
    #end while
#end main
    
   

if __name__ == "__main__":
    main()