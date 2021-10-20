import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from urllib import parse

import requests
from rich import print
from rich.console import Console
from rich.progress import Progress
from rich.progress import track
from selenium import webdriver

console = Console()


class qqzone_upload(object):
    def __init__(self, path):
        self.path = path

    def _login_and_wait(self):
        opt = webdriver.ChromeOptions()

        self.driver = webdriver.Chrome(chrome_options=opt)
        self.driver.get("https://i.qq.com")

        while True:
            url = self.driver.current_url
            if "user.qzone.qq.com" in url:
                time.sleep(0.2)
                self.my_uin = str(url[url.rfind("/") + 1 :])
                self.cookies = self.driver.get_cookies()
                self.g_tk = str(
                    self.driver.execute_script("return QZONE.FP.getACSRFToken()")
                )
                break
            else:
                time.sleep(1)

    def _init_session(self):
        self.session = requests.Session()
        for cookie in self.cookies:
            self.session.cookies.set(cookie["name"], cookie["value"])
        self.session.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"
        }

    def _add_ablum_and_get_id(self):
        ablum_name = self.path[self.path.rfind("\\") + 1 :]
        print(ablum_name)
        url = (
            "https://user.qzone.qq.com/proxy/domain/photo.qzone.qq.com/cgi-bin/common/cgi_add_album_v2?g_tk="
            + self.g_tk
        )
        data = (
            "inCharset=utf-8&outCharset=utf-8&hostUin="
            + self.my_uin
            + "&notice=0&callbackFun=_Callback&format=fs&plat=qzone&source=qzone&appid=4&uin="
            + self.my_uin
            + "&album_type=&birth_time=&degree_type=0&enroll_time=&albumname="
            + parse.quote(ablum_name.encode("utf-8"))
            + "&albumdesc=&albumclass=100&priv=3&queFstion=&answer=&whiteList=&bitmap=10000000&qzreferrer=https%3A%2F%2Fuser.qzone.qq.com%2F201001948%2F4"
        )
        r = self.session.post(url, data, verify=False)
        self.id = (r.text[r.text.find('"id" : ') + 8 :])[
            : (r.text[r.text.find('"id" : ') + 8 :]).find('",')
        ]
        print(self.id)

    def _add_the_photo(self, photo_name):
        photo_path = self.path + "\\" + photo_name
        self.driver.find_element_by_xpath('//*[@id="container"]/div/a/input').send_keys(
            photo_path
        )

    def _input_all_added(self):
        self.driver.find_element_by_xpath('//input[@_phototype="2"]').click()
        self.driver.find_element_by_xpath(
            '//a[@class="op-btn btn-upload j-btn-start j-uploading-hide"]'
        ).click()
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("tphoto")
        while True:
            try:
                self.driver.find_element_by_xpath(
                    '//span[contains(text(), "继续上传")]'
                ).click()
            except:
                try:
                    self.driver.find_element_by_xpath('//a[@id="back_upload"]').click()
                    time.sleep(3)
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame("photoUploadDialog")
                    break
                except BaseException as e:
                    time.sleep(3)

    def _input_photos(self):
        self.driver.switch_to.frame("photoUploadDialog")
        # str = '//li[@_aid="' + self.id + '"]'
        # self.driver.find_element_by_xpath(str).click()

        """
        num=len(self.name_lists)
        num2=num%500
        num1=num//500

        for i in track(range(num1),"Uploading..."):
            for j in range(i*500,i*500+500,1):
                self._add_the_photo(self.name_lists[j])
            self._input_all_added()

        if num2!=0:
            for i in range(num2):
                self._add_the_photo(self.name_lists[i+num1])
            self._input_all_added()
        """

        for i in track(range(len(self.name_lists) - self.start_num), "Uploading..."):
            self._add_the_photo(self.name_lists[i + self.start_num])
            if (i + 1) % 500 == 0 or (i + 1 + self.start_num) >= len(self.name_lists):
                self._input_all_added()

    def _make_name_list(self):
        g = os.walk(self.path)
        for path, dir_list, file_list in g:
            self.name_lists = file_list
            # print(file_list)

    def start_at(self, num=0, make_ablum=False):
        self.start_num = num
        self._make_name_list()
        self._login_and_wait()
        if make_ablum or num == 0:
            self._init_session()
            self._add_ablum_and_get_id()
        wait = input("wait")
        self._input_photos()
        self.driver.quit()
