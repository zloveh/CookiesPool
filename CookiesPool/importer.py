# -*- coding: utf-8 -*-
from CookiesPool.db import RedisClient

conn = RedisClient("accounts", "weibo")

def set(account, sep=':'):
    username, password = account.split(sep)
    result = conn.set(username, password)
    print('账号', username, '密码', password)
    print('录入成功' if result else print('录入失败'))

def scan():
    print("请输入账号密码，以':'分隔,输入exit退出读入")
    while True:
        accpunt = input()
        if accpunt == 'exit':
            break
        set(accpunt)


if __name__ == '__main__':
    scan()