# -*- coding: utf-8 -*-
from selenium import webdriver

# 导入期望类
from selenium.webdriver.support import expected_conditions as EC

# 导入By类
from selenium.webdriver.common.by import By

# 导入显式等待类
from selenium.webdriver.support.ui import WebDriverWait

# 导入异常类
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from selenium.webdriver import ActionChains
from PIL import Image
from io import BytesIO
import time
from os import listdir
from os.path import dirname

# 获得文件当前路径os.path.abspath，获得文件的父目录os.path.dirname
# __FILE__是一个预定义变量，返回的是文件所在的路径；
# d = abspath(__file__)         # C:\Users\账套\‪Desktop\untitled\CookiesPool\weibo\getCookies.py
# f = dirname(__file__)         # C:/Users/账套/‪Desktop/untitled/CookiesPool/weibo

TEMPLATES_FOLDER = dirname(__file__) + "/image/"


class WeiboCookies(object):

    def __init__(self, username, password, driver):
        self.url = "https://passport.weibo.cn/signin/login"
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10, 0.5)
        self.username = username
        self.password = password

    def open(self):
        """
        打开网页输入账号密码，并点击
        :return:
        """
        self.driver.get(self.url)
        username = self.wait.until(EC.presence_of_element_located((By.ID, "loginName")))
        password = self.wait.until(
            EC.presence_of_element_located((By.ID, "loginPassword"))
        )
        button = self.wait.until(EC.element_to_be_clickable((By.ID, "loginAction")))
        username.send_keys(self.username)
        password.send_keys(self.password)
        time.sleep(1)
        button.click()

    def password_error(self):
        """
        判断账号，密码是否出错
        :return:
        """
        try:
            return WebDriverWait(self.driver, 5).until(
                EC.text_to_be_present_in_element((By.ID, "errorMsg"), "用户名或密码错误")
            )
        except TimeoutException:
            return False

    def login_successfully(self):
        """
        判断是否登录成功
        :return:
        """
        try:
            return bool(
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "drop-title"))
                )
            )
        except TimeoutException:
            return False

    def get_position(self):
        """
        获取验证码位置
        :return:
        """
        try:
            img = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#patternCaptchaHolder .patt-holder-body")
                )
            )
        except TimeoutException:
            print("未出现验证码")
            self.open()
            img = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#patternCaptchaHolder .patt-holder-body")
                )
            )
        except NoSuchElementException as e:
            print(e.args)
            self.open()
            img = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#patternCaptchaHolder .patt-holder-body")
                )
            )
        time.sleep(2)
        location = img.location
        size = img.size
        top, bottom, left, right = (
            location["y"],
            location["y"] + size["height"],
            location["x"],
            location["x"] + size["width"],
        )

        return (top, bottom, left, right)

    def get_image(self, name="captcha.png"):
        """
        获取验证码图片
        :param name: 验证码图片名字
        :return:
        """
        top, bottom, left, right = self.get_position()
        # 获取整个网页截图
        screenahot = self.driver.get_screenshot_as_png()
        # 将截图读到内存
        screenahot = Image.open(BytesIO(screenahot))
        # 截取验证码图片
        captcha = screenahot.crop((left, top, right, bottom))
        # captcha.show()
        captcha.save(name)
        return captcha

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: x坐标
        :param y: y坐标
        :return: True or Flase
        """
        threshold = 20
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]

        if (
            abs(pixel1[0] - pixel2[0]) < threshold
            and abs(pixel1[1] - pixel2[1]) < threshold
            and abs(pixel1[2] - pixel1[1]) < threshold
        ):
            return True
        return False

    def same_image(self, image, template):
        """
        识别相似验证码
        :param image:待识别验证码
        :param template: 模板
        :return: True or Flase
        """
        # 相似度阈值
        threshold = 0.99
        count = 0
        for x in range(image.width):
            for y in range(image.height):
                if self.is_pixel_equal(image, template, x, y):
                    count += 1
        result = float(count) / (image.width * image.height)
        if result > threshold:
            print("成功匹配")
            return True
        else:
            return False

    def detect_image(self, image):
        """
        匹配图片
        :param image: 图片
        :return: 拖动顺序
        """
        for template_name in listdir(TEMPLATES_FOLDER):
            print("正在匹配", template_name)
            template = Image.open(TEMPLATES_FOLDER + template_name)
            if self.same_image(image, template):
                # 返回顺序
                numbers = [int(number) for number in list(template_name.split(".")[0])]
                print("拖动顺序", numbers)
                return numbers

    def move(self, numbers):
        """
        根据顺序拖动
        :param numbers:
        :return:
        """
        # 获得四个按点
        try:
            circles = self.driver.find_elements_by_css_selector(".patt-wrap .patt-circ")
            dx = dy = 0
            for index in range(4):
                # 获取相对应的按点
                circle = circles[numbers[index] - 1]
                # 如果是第一个按点
                if index == 0:
                    # 点击不放
                    ActionChains(self.driver).move_to_element_with_offset(
                        circle, circle.size["width"] / 2, circle.size["height"] / 2
                    ).click_and_hold().perform()
                else:
                    # 小幅移动次数
                    times = 30
                    for i in range(times):
                        ActionChains(self.driver).move_by_offset(
                            dx / times, dy / times
                        ).perform()
                        time.sleep(1 / times)
                # 如果这是最后一次循环
                if index == 3:
                    # 松开鼠标
                    ActionChains(self.driver).release().perform()
                else:
                    # 计算下一次偏移
                    dx = (
                        circles[numbers[index + 1] - 1].location["x"] - circle.location["x"]
                    )
                    dy = (
                        circles[numbers[index + 1] - 1].location["y"] - circle.location["y"]
                    )
        except:
            return False

        time.sleep(2)
        # 再次点击登录按钮，登录
        button = self.wait.until(EC.element_to_be_clickable((By.ID, "loginAction")))
        button.click()

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


if __name__ == "__main__":
    # gs = GetSlide("18238766571", "123456789")
    gs = WeiboCookies('13323800669', '20151554209')
    result = gs.run()
    print(result)
