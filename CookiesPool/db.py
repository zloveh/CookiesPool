# -*- coding: utf-8 -*-
import random
import redis
from CookiesPool.config import *


class RedisClient(object):

    def __init__(
        self, type, website, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD
    ):
        """
        初始化redis连接
        :param type: accounts(账号) or cookies
        :param website: website(网站)
        :param host: 地址
        :param port: 端口
        :param password: 密码
        """
        self.db = redis.StrictRedis(
            host=host, port=port, password=password, decode_responses=True
        )
        self.type = type
        self.website = website

    def name(self):
        """
        获取Hash名称
        :return: Hash名称
        """
        return "{type}:{website}".format(type=self.type, website=self.website)

    def set(self, username, value):
        """
        设置键值对
        :param username: 用户名
        :param value: 密码或者cookies
        :return:
        """
        return self.db.hset(self.name(), username, value)

    def get(self, username):
        """
        根据键名获取键值
        :param username:用户名
        :return: 键值
        """
        return self.db.hget(self.name(), username)

    def delete(self, username):
        """
        根据键名删除键值对
        :param username: 用户名
        :return:
        """
        self.db.hdel(self.name(), username)

    def count(self):
        """
        获取数目
        :return: 数目
        """
        return self.db.hlen(self.name())

    def random(self):
        """
        随机得到键值，用于随机cookies的获取
        :return: 随机cookies
        """
        return random.choice(self.db.hvals(self.name()))

    def usernames(self):
        """
        获取所有账户信息
        :return: 所有用户名
        """
        return self.db.hkeys(self.name())

    def all(self):
        """
        获取所有键值对
        :return: 用户名和密码 或者 cookies的映射表
        """
        return self.db.hgetall(self.name())
