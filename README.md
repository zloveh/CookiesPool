# CookiesPool搭建   
&nbsp;&nbsp;&nbsp;&nbsp;以新浪微博为目标，登录新浪微博获取Cookies搭建Cookies池。Cookies池分为4个模块：
* 存储模块
* 获取模块
* 检测模块
* 接口模块  
登录微博的方法见：WeiBo_login, 以WeiBo_login为基础进行登录，搭建Cookies池。  
1. 存储模块：  
需要存储的内容是账号信息，和Cookies信息，也就是账号和密码， 账号和对应的cookies值，这是两组映射，所以选用redis的Hash，建立两个Hash  
![图1](https://github.com/zloveh/CookiesPool/blob/master/1.png)    
![图2](https://github.com/zloveh/CookiesPool/blob/master/2.png)  
Hash的key就是账号，value是密码或者Cookies
```
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
```
详细代码见： db.py  

向数据库插入账号密码  
```
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
``` 
详细代码：importer.py  
2. 获取模块:  
登录方式WeiBo_login已经讲解， 为了获取Cookies，对其做下修改  
```

    def get_cookies(self):
        """
        获取cookies值
        :return:
        """
        return self.driver.get_cookies()

    def run(self):
        """
        主函数
        :return:
        """
        self.open()
        if self.password_error():
            return {"status": 2, "content": "用户名或密码错误"}
        # 如果不需要验证码直接登录成功
        if self.login_successfully():
            cookies = self.get_cookies()
            return {"status": 1, "content": cookies}
        image = self.get_image()
        numbers = self.detect_image(image)
        self.move(numbers)
        if self.login_successfully():
            cookies = self.get_cookies()
            return {"status": 1, "content": cookies}
        else:
            return {"status": 3, "content": "登录失败"}
```  
详细代码： getCookies.py  
  
获取Cookies  
```
    def new_cookies(self, username, password):
        """
        生成Cookies
        :param username: 用户名
        :param password: 密码
        :return: 用户名和Cookies
        """
        return WeiboCookies(username, password, self.browser).run()

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
```
 详细代码： generator.py  

 3. 检测模块：
 ```
  def test(self, username, cookies):
        print('正在测试Cookies', '用户名', username)
        try:
            cookies = json.loads(cookies)
        except TypeError:
            print('Cookies不合法', username)
            self.cookies_db.delete(username)
            print('删除Cookies', username)
            return
        try:
            test_url = TEST_URL_MAP[self.website]
            response = requests.get(test_url, cookies=cookies, timeout=5, allow_redirects=False)
            if response.status_code == 200:
                print('Cookies有效', username)
            else:
                print(response.status_code, response.headers)
                print('Cookies失效', username)
                self.cookies_db.delete(username)
                print('删除Cookies', username)
        except ConnectionError as e:
            print('发生异常', e.args)
 ```  

 4. 接口模块：
 定义一个Web接口，使用Flask实现随机Cookies
 ```
 @app.route('/<website>/random')
def random(website):
    """
    获取随机的Cookie, 访问地址如 /weibo/random
    :return: 随机Cookie
    """
    g = get_conn()
    cookies = getattr(g, website + '_cookies').random()
    return cookies
 ```  
 详细代码：api.py

 最后添加一个调度模块，调度四个模块,使用多进程，使得Cookies生成与Cookies检测模块同时运行：
 ```
 class Scheduler(object):
    @staticmethod
    def valid_cookie(cycle=CYCLE):
        while True:
            print('Cookies检测进程开始运行')
            try:
                for website, cls in TESTER_MAP.items():
                    tester = eval(cls + '(website="' + website + '")')
                    tester.run()
                    print('Cookies检测完成')
                    del tester
                    time.sleep(cycle)
            except Exception as e:
                print(e.args)

    @staticmethod
    def generate(cycle=CYCLE):
        while True:
            print('Cookies生成进程开始运行')
            try:
                for website, cls in GENERATOR_MAP.items():
                    generator = eval(cls + '(website="' + website + '")')
                    generator.run()
                    print('Cookies生成完成')
                    generator.close()
                    time.sleep(cycle)
            except Exception as e:
                print(e.args)

    @staticmethod
    def api():
        while True:
            print('API模块开始运行')
            app.run(host=API_HOST, port=API_PORT)

    def run(self):
        if API_PROCESS:
            api_process = Process(target=Scheduler.api)
            api_process.start()

        if GENERATOR_PROCESS:
            generator_process = Process(target=Scheduler.generate)
            generator_process.start()

        if VALID_PROCESS:
            valid_process = Process(target=Scheduler.valid_cookie)
            valid_process.start()
 ```
详细代码： scheduler.py
