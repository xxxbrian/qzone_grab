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


class qqzone_get(object):
    def __init__(self):
        self.host_uin = "176842"  # '176842'
        self.download_path = os.getcwd() + "\\dowload\\" + self.host_uin + "\\"
        self.log_switch = "OFF"  # ON or OFF

    def _erro_log(self, str="OFF"):
        if self.log_switch == "ON":
            console.log(str)

    def _login_and_get_args(self):
        """扫码验证获取cookie和g_tk"""
        opt = webdriver.ChromeOptions()

        driver = webdriver.Chrome(chrome_options=opt)
        driver.get("https://i.qq.com")

        while True:
            url = driver.current_url
            if "user.qzone.qq.com" in url:
                time.sleep(0.2)
                self.my_uin = url[url.rfind("/") + 1 :]
                self.cookies = driver.get_cookies()
                self.g_tk = driver.execute_script("return QZONE.FP.getACSRFToken()")
                driver.quit()
                console.log("Account: ", self.my_uin, " Target: ", self.host_uin)
                console.log("LOG:", self.log_switch)
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

    def _get_query_for_request(
        self, topicId=None, pageStart=0, pageNum=500, format="json"
    ):
        """请求信息所需参数"""

        """
        # 相册
        https://user.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3?
        g_tk=858917926& -# must
        callback=shine1_Callback&
        t=903462365&
        hostUin=176842& -# must
        uin=201001948& -# must
        appid=4& - # must
        inCharset=utf-8& -# better 
        outCharset=utf-8& -# better
        source=qzone& -# better
        plat=qzone& -# better
        format=jsonp& -# 如果将请求参数中的format由jsonp改成json，则可以直接获取json数据
        notice=0&
        filter=1&
        handset=4&
        pageNumModeSort=40&
        pageNumModeClass=15&
        needUserInfo=1&
        idcNum=4&
        mode=2&
        sortOrder=1&
        pageStart=30& -# must need be 0
        pageNum=32& -# must need be max (500)
        callbackFun=shine3&
        _=1609336004698

        # 照片
        https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo?
        g_tk=858917926& 
        callback=shine3_Callback&
        t=965028233&mode=0&
        idcNum=4&
        hostUin=176842&
        topicId=sa32V5259ZZY1b0ctB1LDYsq0OoAiq4DFP2x323697614050b2b55b681cf7ff496f4ee514V129IDtg00qjPU&
        noTopic=0&
        uin=201001948&
        pageStart=60&
        pageNum=30&
        skipCmtCount=0&
        singleurl=1&
        batchId=&
        notice=0&
        appid=4&
        inCharset=utf-8&
        outCharset=utf-8&
        source=qzone&
        plat=qzone&
        outstyle=json&
        format=jsonp&
        json_esc=1&
        callbackFun=shine3&
        _=1609345707025
        """

        query = {
            "g_tk": self.g_tk,
            "hostUin": self.host_uin,
            "uin": self.my_uin,
            "appid": 4,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "source": "qzone",
            "plat": "qzone",
            "format": format,
            "pageStart": pageStart,
            "pageNum": pageNum,
        }
        if topicId:
            query["topicId"] = topicId
        return "&".join("{}={}".format(key, val) for key, val in query.items())

    def _get_album_list(self):
        album_get_url = "{}{}".format(
            "https://user.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/fcg_list_album_v3?",
            self._get_query_for_request(),
        )

        print("[bold dark_orange3]\nFuncation: GET ALBUM LIST[/bold dark_orange3]")
        resp = self.session.get(album_get_url)

        data = json.loads(
            resp.text[
                resp.text.find("{", 1) : resp.text.rfind("}", 0, len(resp.text) - 1)
            ]
        )

        album_name_list = []
        for item in data["albumListModeSort"]:
            album_name_list.append(str(item["name"]))
        album_id_list = []
        for item in data["albumListModeSort"]:
            album_id_list.append(str(item["id"]))
        album_total_list = []
        for item in data["albumListModeSort"]:
            album_total_list.append(str(item["total"]))
        album_priv_list = []
        for item in data["albumListModeSort"]:
            album_priv_list.append(str(item["priv"]))

        album_list = list(
            zip(album_id_list, album_name_list, album_total_list, album_priv_list)
        )

        return album_list

    def _get_photo_url(self, album_name, album_id, album_total):
        album_total = int(album_total)
        album_name = (
            album_name.replace("<", "")
            .replace(">", "")
            .replace("?", "")
            .replace("*", "")
            .replace("/", "")
            .replace('"', "")
            .replace("|", "")
        )

        path = self.download_path + album_name + "\\"
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)
            print(
                "[bold navajo_white1]" + album_name + "[/bold navajo_white1]",
                "[italic dark_orange3] GET PHOTO LIST[/italic dark_orange3]",
            )

        else:
            print(
                "[bold navajo_white1]" + album_name + "[/bold navajo_white1]",
                "[italic dark_orange3] GET PHOTO LIST[/italic dark_orange3]"
                + " Exisits",
            )

        photo_url_list = []
        photo_sloc_list = []
        for i in track(range(math.ceil(album_total / 500)), "Loading URL..."):
            while True:
                try:
                    photo_get_url = "{}{}".format(
                        "https://h5.qzone.qq.com/proxy/domain/photo.qzone.qq.com/fcgi-bin/cgi_list_photo?",
                        self._get_query_for_request(
                            topicId=album_id,
                            pageStart=i * 500,
                            pageNum=500,
                        ),
                    )
                    resp = self.session.get(photo_get_url)
                    data = json.loads(resp.text)

                    for item in data["data"]["photoList"]:
                        photo_url_list.append(str(item["url"]))
                    for item in data["data"]["photoList"]:
                        photo_sloc_list.append(str(item["sloc"]))
                except:
                    self._erro_log("Loading ERRO, Fixing...")

                else:
                    break

        photo_list = list(zip(photo_url_list, photo_sloc_list))
        """多线程下载"""

        with Progress() as task_dow:
            task_id = task_dow.add_task(description="Downloading...", total=album_total)
            with ThreadPoolExecutor() as executor:  # 创建 ThreadPoolExecutor
                for i in photo_list:
                    executor.submit(
                        self._download_image,
                        i[0],
                        path + i[1] + ".jpg",
                        task_id,
                        task_dow,
                    )

    def _download_image(self, url, path, task_id, task_dow):
        """下载图片-子线程"""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                open(path, "wb").write(resp.content)
        except requests.exceptions.Timeout:
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    open(path, "wb").write(resp.content)
            except:
                self._erro_log("Downloading ERRO: TIME OUT")
                self._erro_log("erro url is:" + url + "\nPassing...")

        except requests.exceptions.ConnectionError as e:
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code == 200:
                    open(path, "wb").write(resp.content)
            except:
                self._erro_log("Downloading ERRO:\n" + str(e))
                self._erro_log("erro url is:" + url + "\nPassing...")
        finally:
            task_dow.update(task_id, advance=1)

    def start(self):
        self._login_and_get_args()
        self._init_session()
        album_list = self._get_album_list()
        for i in range(0, len(album_list), 1):
            if album_list[i][3] == "1":
                self._get_photo_url(
                    album_name=album_list[i][1],
                    album_id=album_list[i][0],
                    album_total=album_list[i][2],
                )
