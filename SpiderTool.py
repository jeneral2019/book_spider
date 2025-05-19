import requests
import time
from Log import Log
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from lxml import html
import bisect


log = Log('spider')

RULES = [
    {
        "url": ["https://www.bqgl.cc", "https://www.mac3.cc"],
        "search": {
            'search_url': "https://www.bqgl.cc/user/search.html?q={}",
            'url_list': "url_list"
        },
        "rule": {
            "name": "#info>h1",
            "toc": ".listmain dd a",
            "content": "#content"
        }
    },
]


class Req:
    default_user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/129.0.0.0 Safari/537.36')
    log = Log('req')

    @staticmethod
    def req(url):
        headers = {'User-Agent': Req.default_user_agent}
        e = 0
        while e < 100:
            try:
                r = requests.get(url, timeout=(6, 30), headers=headers)
                if r.status_code == 200:
                    return r
                elif r.status_code == 404:
                    log.error("网址错误404: " + url)
                    raise ValueError("网址错误: " + url)
                else:
                    e = e + 1
                    log.debug(f"[{e}]: request error:" + str(r.status_code))
            except Exception as Ex:
                e = e + 1
                log.debug(f"[{e}]: request error: {Ex}")
                time.sleep(1)


class SpiderTool:

    def __init__(self):
        pass

    def smart_select(self, tree, selector):
        """
        根据 selector 自动判断使用 xpath 还是 css 查询。
        :param tree: lxml 的 ElementTree 对象
        :param selector: 查询表达式（XPath 或 CSS）
        :return: 查询结果列表
        """
        selector = selector.strip()
        if selector.startswith('xpath:'):
            return tree.xpath(selector.split('xpath:')[-1])
        else:
            return tree.cssselect(selector)

    def search(self, book_name):
        # 查找小说
        toc_url = None
        for rule in RULES:
            if 'search' in rule:
                search_url = rule['search']['search_url'].format(book_name)
                result = Req.req(search_url)
                result_json = json.loads(result.text)
                if len(result_json) == 0:
                    log.error('无法搜索到结果')
                    continue
                if len(result_json) > 1:
                    log.info('搜索结果超过一个，取第一个结果')
                url_list = result_json[0].get(rule['search']['url_list'])
                if url_list.startswith('/'):
                    toc_url = rule['url'] + url_list
                else:
                    toc_url = url_list
                break
        return toc_url

    def spider_toc(self, toc_url, rule=None):
        parsed = urlparse(toc_url)
        base_url = f'{parsed.scheme}://{parsed.netloc}'
        if rule is None:
            for r in RULES:
                if 'url' in r and base_url in r['url']:
                    rule = r['rule']
                    break
        # 爬目录
        toc_result = Req.req(toc_url)
        toc_result.encoding = toc_result.apparent_encoding
        tree = html.fromstring(toc_result.text)

        if 'toc_is_next' in rule:
            titles = []
            while True:
                titles.extend(self.smart_select(tree, rule['toc']))
                if self.smart_select(tree, rule['toc_is_next'])[-1].text != '下一页':
                    break
                soup = BeautifulSoup(Req.req(base_url + self.smart_select(tree, rule['toc_is_next'])[-1].get('href')).text,
                                     features="html.parser")
        else:
            titles = self.smart_select(tree, rule['toc'])
        catalog = []
        for title in titles:
            cid = title.attrib["href"].rsplit('/', 1)[-1].rsplit('.', 1)[0].zfill(5)
            name = title.text.strip()
            href = title.attrib["href"].strip()
            chapter_link = {'id': cid, 'title': name, 'href': href, 'is_checked': False}
            if not any(item['id'] == chapter_link['id'] for item in catalog):
                bisect.insort(catalog, chapter_link, key=lambda x: x['id'])
        return catalog

    def download(self):
        pass


if __name__ == '__main__':
    # a = SpiderTool().search(book_name='来自星渊')
    # print(a)
    SpiderTool().spider_toc("https://www.mac3.cc/read/119046/")
