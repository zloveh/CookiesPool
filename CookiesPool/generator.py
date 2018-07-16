# -*- coding: utf-8 -*-
import json
from selenium import webdriver

# 配置webdriver在指定的环境执行我们的测试脚本
from selenium.webdriver import DesiredCapabilities
from CookiesPool.config import *
from CookiesPool.db import RedisClient
from CookiesPool.weibo.getCookies import WeiboCookies


class CookiesGenerator(object):

    def __init__(self, website="default"):
        """
        父类, 初始化一些对象
        :param website:
        """
        self.website = website
        self.cookies_db = RedisClient("cookies", self.website)
        self.accounts_db = RedisClient("accounts", self.website)
        self.init_browser()

    def __del__(self):
        self.close()

    def init_browser(self):
        """
        通过browser参数初始化全局浏览器供模拟登陆使用
        :return:
        """
        if BROWSER_TYPE == "PhantomJS":
            caps = DesiredCapabilities.PHANTOMJS
            caps[
                "phantomjs.page.settings.userAgent"
            ] = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
            )
            self.browser = webdriver.PhantomJS(desired_capabilities=caps)
            self.browser.set_window_size(1400, 500)
        if BROWSER_TYPE == "Chrome":
            self.browser = webdriver.Chrome()

    def new_cookies(self, username, password):
        '''
        新生成cookies， 子类需要重写
        :param username:
        :param password:
        :return:
        '''
        raise NotImplementedError

    def process_cookies(self, cookies):
        '''
        处理cookies
        :param cookies:
        :return:
        '''
        dict = {}
        for cookie in cookies:
            dict[cookie['name']] = cookie['value']
        return dict

    def run(self):
        '''
        运行， 获取所有账号， 然后顺次模拟登陆
        :return:
        '''
        accounts_usernames = self.accounts_db.usernames()
        cookies_usernames = self.cookies_db.usernames()

        for username in accounts_usernames:
            if username not in cookies_usernames:
                password = self.accounts_db.get(username)
                print('正在生成cookies', '账号', username, '密码', password)
                result = self.new_cookies(username, password)
                if result.get('status') == 1:
                    cookies = self.process_cookies(result.get('content'))
                    print('成功获取cookies', cookies)
                    self.cookies_db.set(username, json.dumps(cookies))
                    print('成功保存cookies')
                # 密码错误，移除账号
                elif result.get('status') == 2:
                    print(result.get('content'))
                    if self.accounts_db.delete(username):
                        print('成功删除账号')
                else:
                    print(result.get('content'))
        else:
            print('所有账号都已经成功获取Cookies')

    def close(self):
        '''
        关闭
        :return:
        '''
        try:
            print('Closing Browser')
            self.browser.close()
            del self.browser
        except TypeError:
            print('Browser not opened')


class WeiboCookiesGenerator(CookiesGenerator):
    def __init__(self, website='weibo'):
        CookiesGenerator.__init__(self, website)
        self.website = website

    def new_cookies(self, username, password):
        """
        生成Cookies
        :param username: 用户名
        :param password: 密码
        :return: 用户名和Cookies
        """
        return WeiboCookies(username, password, self.browser).run()


if __name__ == '__main__':
    generator = WeiboCookiesGenerator()
    generator.run()


