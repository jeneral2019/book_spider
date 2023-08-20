"""
@author jeneral
@date 2023/8/16 10:53
@desc 
"""
from dotenv import load_dotenv
import time
import requests
from bs4 import BeautifulSoup
import re

# 加载 .env 文件
load_dotenv()

'''
模板
爬虫所需素材
1. base_url
2. 小说目录地址
3. 爬虫规则

爬虫规则
1. toc          目录
2. toc_fix      目录处理
3. content      小说内容
4. content_fix  小说内容处理
5. is_next      判断该章是否未爬完

rule = {
    "toc": ".container.border3-2.mt8.mb20>a",
    "content": "#article",
    "is_next": "#next_url"
}
'''


def req(url):
    e = 0
    while e < 100:
        try:
            r = requests.get(url, timeout=(6, 30))
            if r.status_code == 200:
                break
            elif r.status_code == 404:
                raise ValueError("网址错误: " + url)
            else:
                e = e + 1
                print("request error:" + str(r.status_code))
        except Exception as Ex:
            e = e + 1
            print(Ex)
            time.sleep(1)
    return r


def spider_books(base_url, toc_url, filename, rules):
    r = req(toc_url)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, features="html.parser")
    titles = soup.select(rules["toc"])
    for title in titles:
        r_title = prefix_title(title.text)
        d = req(base_url + title.get('href'))
        d.encoding = d.apparent_encoding
        d_text = ''
        while True:
            d_soup = BeautifulSoup(d.text, features="html.parser")
            for t in d_soup.select(rules["content"]):
               d_text = d_text + '\t' + t.text + '\n'
            if d_soup.select(rules["is_next"])[-1].text.find('下一页') < 0:
                break
            d = req(base_url + d_soup.select('#next_url')[-1].get('href'))

        try:
            with open(filename, 'a', encoding=r.encoding) as f:
                f.write(r_title + '\n')
                print(r_title)
                f.write(d_text.replace('     ', '\t') + '\n\n')
        finally:
            f.close()


def prefix_title(title_str):
    pattern = r"^\S+\s"  # 匹配第一个空格之前的非空白字符
    match = re.search(pattern, title_str)
    if match is None:
        return title_str + '\n'
    if match:
        data = match.group(0)
        if not data.startswith("第"):
            title_str = re.sub(r"^(\S+)", r"第\1", title_str)
        if not data.endswith("章 "):
            title_str = re.sub(r"^(\S+)", r"\1章", title_str)
        return title_str + '\n'


if __name__ == '__main__':

    rule = {
        "toc": ".container.border3-2.mt8.mb20>.info-chapters.flex.flex-wrap>a",
        "content": "#article>p",
        "is_next": "#next_url"
    }
    spider_books("https://www.ibiqiuge.com", 'https://www.ibiqiuge.com/99520/', "星门.txt", rule)

    # title = '001 优秀市民马修和天杀的死灵法师'
    # print(prefix_title(title))
    # title2 = '第001章 优秀市民马修和天杀的死灵法师'
    # print(prefix_title(title2))
    # title3 = '第001章优秀市民马修和天杀的死灵法师'
    # print(prefix_title(title3))
