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
import os
import json
from urllib.parse import urlparse

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
    "name": ".w100>h1",
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


def spider_books(base_url, toc_url, rule):
    # 规则检查
    check_rule(rule)

    r = req(toc_url)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, features="html.parser")
    filename = soup.select(rule["name"])[0].text + '.txt'
    titles = soup.select(rule["toc"])
    for title in titles:
        r_title = prefix_title(title.text)
        d = req(base_url + title.get('href'))
        d.encoding = d.apparent_encoding
        d_text = ''
        while True:
            d_soup = BeautifulSoup(d.text, features="html.parser")
            for t in d_soup.select(rule["content"]):
               d_text = d_text + '\t' + t.text + '\n'
            if d_soup.select(rule["is_next"])[-1].text.find('下一页') < 0:
                break
            d = req(base_url + d_soup.select('#next_url')[-1].get('href'))

        try:
            with open(get_download_path() + filename, 'a', encoding=r.encoding) as f:
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


def find_rules(book_toc_url: str):
    # 获取base_url
    parsed_url = urlparse(book_toc_url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc

    # 遍历已有规则，查看是否有匹配数据
    rules = json.loads(os.getenv("RULES"))
    for rule in rules:
        if rule['url'] == base_url:
            return rule['url'], book_toc_url, rule['rule']
    raise ValueError("找不到该网址的规则: " + book_toc_url)


def get_download_path():
    download_path = os.getenv("DOWNLOAD_PATH")
    if download_path is None:
        # 设置默认路径
        download_path = os.getenv("HOME") + '/Downloads'
    # 若配置路基采用了相对路径，转换成绝对路径
    elif download_path.startswith('~'):
        download_path = download_path.replace('~', os.getenv("HOME"))
    if os.path.isdir(download_path):
        return download_path + '/'
    else:
        raise ValueError('DOWNLOAD_PATH配置错误，请检查({})'.format(download_path))


def check_rule(rule):
    # name、toc、content 必须要有
    if rule['name'] is None or rule['toc'] is None or rule['content'] is None:
        raise ValueError('规则错误 {}'.format(rule))


def get_search_rule(rule):
    return rule['search']


def search(search_text):
    results = []
    rules = json.loads(os.getenv("RULES"))
    for r1 in rules:
        rule = r1['rule']
        if rule['search'] is None or rule['search']['search_url'] is None or rule['search']['search_request'] is None:
            continue
        data = {k: search_text if v == '#text' else v for k, v in rule['search']['search_request'].items()}
        r = requests.post(rule['search']['search_url'], data=data)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, features="html.parser")
        book_names = soup.select(rule['search']["book_name"])
        book_urls = soup.select(rule['search']["book_url"])
        results.append({r1['url'] + k.get('href'): v.text for k, v in zip(book_urls, book_names)})
    return results


if __name__ == '__main__':
    # base_url, toc_url, rule = find_rules('https://www.ibiqiuge.com/96478/')
    # spider_books(base_url, toc_url, rule)
    # print(get_search_rule(rule))
    print(search('万相'))
