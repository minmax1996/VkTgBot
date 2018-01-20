from Models.User import *


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
