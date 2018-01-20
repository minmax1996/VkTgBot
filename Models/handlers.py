import re


def handle_photo(att,user,b):
    max=int(0)
    for ph in att:
        if(re.fullmatch(r'^photo_[0-9]*',ph)):
            if(int(ph[6:])>max):
                max=int(ph[6:])
    print(max)
    b.send_photo(user.chatid,att['photo_'+str(max)])
    return True

def handle_audio(att,user,b):
    if (att['url']):
        print('got url '+att['url'])
        b.send_audio(user.chatid,att['url'])
    else:
        print('нет url')
    return True

def handle_video(att,user,b):

    return True

def handle_doc(att,user,b):

    return True

def handle_link(att,user,b):
    b.send_message(user.chatid,att['url'])
    return True