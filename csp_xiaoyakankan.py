# coding=utf-8
# 小鸭看看 - TVBox 解析脚本（带自动刷新 m3u8）

import sys
import json
import re
from urllib import parse
import requests
from bs4 import BeautifulSoup

class Spider:
    def __init__(self):
        self.baseUrl = "https://xiaoyakankan.com"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                          "AppleWebKit/537.36 (KHTML, like Gecko) " +
                          "Chrome/114.0.0.0 Safari/537.36"
        }

    # 首页分类
    def homeContent(self, filter):
        result = {}
        classes = [
            {"type_id": "10", "type_name": "电影"},
            {"type_id": "11", "type_name": "连续剧"},
            {"type_id": "12", "type_name": "综艺"},
            {"type_id": "13", "type_name": "动漫"},
            {"type_id": "15", "type_name": "福利"}
        ]
        result['class'] = classes
        return result

    # 分类内容
    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.baseUrl}/cat/{tid}.html?page={pg}"
        rsp = requests.get(url, headers=self.header, timeout=10)
        rsp.encoding = "utf-8"
        soup = BeautifulSoup(rsp.text, "html.parser")
        videos = []
        for div in soup.select(".m4-list .item"):
            a = div.select_one("a.link")
            if not a:
                continue
            title = div.select_one(".title").get_text(strip=True)
            pic = a.img.get("data-src") or a.img.get("src")
            href = a["href"]
            videos.append({
                "vod_id": parse.urljoin(self.baseUrl, href),
                "vod_name": title,
                "vod_pic": "https:" + pic if pic.startswith("//") else pic,
                "vod_remarks": div.select_one(".tag2").get_text(strip=True) if div.select_one(".tag2") else ""
            })
        return {"list": videos}

    # 详情内容
    def detailContent(self, array):
        url = array[0]
        rsp = requests.get(url, headers=self.header, timeout=10)
        rsp.encoding = "utf-8"
        soup = BeautifulSoup(rsp.text, "html.parser")
        title = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "未知标题"

        vod = {
            "vod_id": url,
            "vod_name": title,
            "vod_pic": "",
            "vod_play_from": "小鸭看看",
            "vod_play_url": ""
        }

        play_urls = []
        # 播放线路 + 集数
        for a in soup.select(".playlist a"):
            name = a.get_text(strip=True)
            href = a.get("href")
            if href:
                play_urls.append(f"{name}${parse.urljoin(self.baseUrl, href)}")

        vod["vod_play_url"] = "#".join(play_urls)
        return {"list": [vod]}

    # 搜索（留空，可扩展）
    def searchContent(self, key, quick):
        return {"list": []}

    # 播放内容（带自动刷新 m3u8）
    def playerContent(self, flag, id, vipFlags):
        # 如果 id 已经是 m3u8
        if id and (id.endswith(".m3u8") or ".m3u8?" in id):
            return {
                "parse": 0,
                "playUrl": id,
                "url": id,
                "header": {
                    "User-Agent": self.header["User-Agent"],
                    "Referer": self.baseUrl
                }
            }

        # 如果是中间页，重新请求解析
        try:
            rsp = requests.get(id, headers=self.header, timeout=10)
            rsp.encoding = "utf-8"
            html = rsp.text

            # 匹配最新的 m3u8 地址
            m = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html)
            if m:
                m3u8_url = m.group(1)
                return {
                    "parse": 0,
                    "playUrl": m3u8_url,
                    "url": m3u8_url,
                    "header": {
                        "User-Agent": self.header["User-Agent"],
                        "Referer": id
                    }
                }
        except Exception as e:
            print(f"[playerContent] 获取失败: {e}")

        return {
            "parse": 0,
            "playUrl": "",
            "url": "",
            "header": {}
        }


if __name__ == "__main__":
    spider = Spider()
    print(json.dumps(spider.homeContent(False), indent=4, ensure_ascii=False))
