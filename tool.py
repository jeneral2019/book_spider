"""
@author jeneral
@date 2025/02/13 10:53
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
import bisect
from ebooklib import epub
import glob
import aiohttp
import asyncio

load_dotenv()
default_user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/129.0.0.0 Safari/537.36')


# 请求重试
def req(url, proxies, headers=None):
    if headers is None:
        headers = {'User-Agent': default_user_agent}
    if proxies is None:
        proxies = {'http': None, 'https': None}
    e = 0
    while e < 100:
        try:
            r = requests.get(url, timeout=(6, 30), proxies=proxies, headers=headers)
            if r.status_code == 200:
                return r
            elif r.status_code == 404:
                raise ValueError("网址错误: " + url)
            else:
                e = e + 1
                print(f"[{e}]: request error:" + str(r.status_code))
        except Exception as Ex:
            e = e + 1
            print(f"[{e}]: request error: {Ex}")
            time.sleep(1)


def find_catalog_by_qi_dian(novel_id, cookie=None):
    novel_url = f"https://www.qidian.com/book/{novel_id}/"
    header = {
        'Cookie': cookie,
        'User-Agent': default_user_agent,
    }
    response = req(novel_url, proxies=None, headers=header)
    soup = BeautifulSoup(response.text, "html.parser")
    book_name = soup.find(id='bookName').text
    author = soup.find(class_='author').text.split("作者:")[1].strip()
    pic_url = 'http:' + soup.find(id='bookImg').img['src']
    all_catalog = []
    for a in soup.select("#allCatalog li a"):
        cid = a['data-cid'].rstrip("/").rsplit("/", 1)[-1]
        chapter_link = {'id': cid, 'title': a.text.strip(), 'href': a["href"]}
        all_catalog.append(chapter_link)
    return book_name, author, pic_url, all_catalog


def find_catalog_by_spider(base_url, toc_url, rule):
    # 规则检查
    if rule['name'] is None or rule['toc'] is None or rule['content'] is None:
        raise ValueError('规则错误 {}'.format(rule))
    if 'proxies' in rule:
        proxies = rule['proxies']
    else:
        proxies = None
    r = req(toc_url, proxies)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, features="html.parser")
    if 'toc_is_next' in rule:
        titles = []
        while True:
            titles.extend(soup.select(rule["toc"]))
            if soup.select(rule["toc_is_next"])[-1].text != '下一页':
                break
            soup = BeautifulSoup(req(base_url + soup.select(rule["toc_is_next"])[-1].get('href'), proxies).text, features="html.parser")
    else:
        titles = soup.select(rule["toc"])
    catalog = []
    for title in titles:
        cid = title["href"].rsplit('/', 1)[-1].rsplit('.', 1)[0]
        name = title.text.strip()
        href = title["href"].strip()
        chapter_link = {'id': cid, 'title': name, 'href': href, 'is_checked': False}
        if not any(item['id'] == chapter_link['id'] for item in catalog):
            bisect.insort(catalog, chapter_link, key=lambda x: x['id'])
    return catalog


def find_rules(book_toc_url: str):
    # 获取base_url
    parsed_url = urlparse(book_toc_url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc

    # 遍历已有规则，查看是否有匹配数据
    rules = json.loads(os.getenv("RULES"))
    for rule in rules:
        if rule['url'] == base_url:
            return rule['url'], rule['rule']
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


def compare_titles(title1, title2, exact_level=0):
    # 去除开头的 "第X章"
    def title_no_chapter(title): return re.sub(r'^第[零一二两三四五六七八九十百千万\d]+章\s*', '', title)
    # 去除括号内内容
    def title_no_parentheses(title): return re.sub(r'[（(].*?[）)]', '', title_no_chapter(title))
    # 去除特殊符号
    def title_no_special(title): return re.sub(r'[^\w\u4e00-\u9fa5]+', '', title_no_parentheses(title))
    if exact_level == 0:
        # 直接对比标题
        return title1 == title2
    elif exact_level == 1:
        # 去除开头的第X章
        return title_no_chapter(title1) == title_no_chapter(title2)
    elif exact_level == 2:
        # 去除括号内容
        return title_no_parentheses(title1) == title_no_parentheses(title2)
    elif exact_level == 3:
        # 去除特殊符号
        return title_no_special(title1) == title_no_special(title2)
    else:
        return (title_no_special(title1) in title_no_special(title2)
                 or title_no_special(title2) in title_no_special(title1))


async def spider_content_async(base_url, content_url, rule):
    if content_url is None:
        raise ValueError('content_url is none')

    async with aiohttp.ClientSession() as session:
        d_text = ''
        current_url = base_url + content_url

        while True:
            # 重试逻辑
            for _ in range(30):
                try:
                    async with session.get(
                        current_url,
                        proxy=rule.get('proxies', {}).get('http'),
                        headers={'User-Agent': default_user_agent},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            break
                        elif response.status == 404:
                            raise ValueError("网址错误: " + current_url)
                        else:
                            print(f"[{_ + 1}]: request error: {response.status}")
                            await asyncio.sleep(1)
                            continue
                except Exception as ex:
                    print(f"[{_ + 1}]: request error: {ex}")
                    await asyncio.sleep(1)
                    continue
            else:
                raise Exception(f"重试30次后仍然失败: {current_url}")

            d_soup = BeautifulSoup(html, features="html.parser")
            for t in d_soup.select(rule["content"]):
                d_text += t.get_text(separator='\n').encode('utf-8', errors='ignore').decode('utf-8')

            if 'is_next' not in rule or d_soup.select(rule["is_next"])[-1].text.find('下一页') < 0:
                break

            current_url = base_url + d_soup.select('#next_url')[-1].get('href')

        return d_text


def spider_desc(novel_id, qi_dian_cookie=None, spider_url=None):
    """
    小说详情
    :param novel_id: 起点novel_id
    :param spider_url:爬虫地址 不填默认从rules中搜索
    :return:
    json:{
        'name': 小说名称,
        'author': 作者,
        'spider_rule': 爬虫规则,
        'spider_base_url': 爬虫基础网址,
        'catalog_list': 章节列表,
    }
    """
    # 爬起点目录
    book_name, author, pic_url, qi_dian_catalog_list = find_catalog_by_qi_dian(novel_id, cookie=qi_dian_cookie)

    # 爬对应网站目录
    spider_base_url, spider_rule = find_rules(spider_url)
    spider_catalog_list = find_catalog_by_spider(spider_base_url, spider_url, spider_rule)

    index = 0
    for qi_dian_catalog in qi_dian_catalog_list:
        index += 1
        qi_dian_catalog['index'] = f'{index:05d}'
    # 目录比对
    for level in range(5):
        for qi_dian_catalog in [x for x in qi_dian_catalog_list if 'spider_url' not in x]:
            for spider_catalog in [x for x in spider_catalog_list if not x['is_checked']]:
                if compare_titles(spider_catalog['title'], qi_dian_catalog['title'], level):
                    qi_dian_catalog['spider_url'] = spider_catalog['href']
                    qi_dian_catalog['spider_name'] = spider_catalog['title']
                    qi_dian_catalog['spider_id'] = spider_catalog['id']
                    spider_catalog['is_checked'] = True
                    break
    spider_catalog_list_len = len(spider_catalog_list)
    qi_dian_catalog_list_len = len(qi_dian_catalog_list)
    for i in range(spider_catalog_list_len):
        if spider_catalog_list[i]['is_checked']:
            continue
        if i == 0:
            if spider_catalog_list[1]['is_checked'] and 'spider_id' in qi_dian_catalog_list[1]:
                qi_dian_catalog_list[0]['spider_url'] = spider_catalog_list[0]['href']
                qi_dian_catalog_list[0]['spider_name'] = spider_catalog_list[0]['title']
                qi_dian_catalog_list[0]['spider_id'] = spider_catalog_list[0]['id']
                spider_catalog_list[0]['is_checked'] = True
                break
            continue
        for j in range(qi_dian_catalog_list_len):
            if j == qi_dian_catalog_list_len - 1:
                if i == spider_catalog_list_len - 1 and spider_catalog_list[-2]['is_checked'] and 'spider_id' in qi_dian_catalog_list[-2]:
                    qi_dian_catalog_list[-1]['spider_url'] = spider_catalog_list[-1]['href']
                    qi_dian_catalog_list[-1]['spider_name'] = spider_catalog_list[-1]['title']
                    qi_dian_catalog_list[-1]['spider_id'] = spider_catalog_list[-1]['id']
                    spider_catalog_list[-1]['is_checked'] = True
                    break
                continue
            if 'spider_id' in qi_dian_catalog_list[j] and spider_catalog_list[i-1]['id'] == qi_dian_catalog_list[j]['spider_id']:
                if 'spider_id' not in qi_dian_catalog_list[j+1]:
                    if (('spider_id' in qi_dian_catalog_list[j+2] and spider_catalog_list[i+1]['is_checked']) or
                            ('spider_id' not in qi_dian_catalog_list[j+2] and not spider_catalog_list[i+1]['is_checked'])):
                        qi_dian_catalog_list[j+1]['spider_url'] = spider_catalog_list[i]['href']
                        qi_dian_catalog_list[j+1]['spider_name'] = spider_catalog_list[i]['title']
                        qi_dian_catalog_list[j+1]['spider_id'] = spider_catalog_list[i]['id']
                        spider_catalog_list[i]['is_checked'] = True
                        break
    return {
        'book_name': book_name,
        'author': author,
        'book_pic': pic_url,
        'spider_rule': spider_rule,
        'spider_base_url': spider_base_url,
        'catalog_list': qi_dian_catalog_list,
    }


def write_desc(novel_id, spider_url=None, qi_dian_cookie=None):
    book_path = get_download_path() + f'/{novel_id}'
    desc_path = book_path + '/desc.json'
    if os.path.exists(desc_path):
        with open(desc_path, 'r', encoding='utf-8') as file:
            desc_json = json.load(file)
            # TODO 重新抓取目录
    else:
        desc_json = spider_desc(novel_id, qi_dian_cookie, spider_url)
        os.makedirs(book_path, exist_ok=True)
        with open(desc_path, 'w', encoding='utf-8') as f:
            json.dump(desc_json, f, ensure_ascii=False, indent=4)


def write_epub(book_id):
    book_path = get_download_path() + f'/{book_id}'
    desc_path = os.path.join(book_path, 'desc.json')

    if not os.path.exists(desc_path):
        raise FileNotFoundError("书籍描述文件 desc.json 不存在")

    with open(desc_path, 'r', encoding='utf-8') as f:
        desc_json = json.load(f)

    book_name = desc_json['book_name']
    author = desc_json['author']

    book = epub.EpubBook()
    book.set_identifier(f'id{book_id}')
    book.set_title(book_name)
    book.set_language('zh')
    book.add_author(author)

    # 添加样式
    css_content = '''
        body {
            display: block;
            text-align: left;
            text-align: justify;
            padding: 0 0 0 0;
            margin: 0 5pt 0 5pt;
        }
        h1 {
            font-size: 100%;
            line-height: 125%;
            margin: 0.5em 0 0.5em 0;
        }
        p {
            font-size: 100%;
            line-height: 120%;
            text-indent: 2em;
            margin: 0.3em 0 0.3em 0em;
        }
    '''
    style = epub.EpubItem(uid="style1", file_name="styles.css", media_type="text/css", content=css_content.encode('utf-8'))
    book.add_item(style)

    # 添加封面
    cover_path = os.path.join(book_path, 'pic.webp')
    if os.path.exists(cover_path):
        with open(cover_path, 'rb') as cover_image:
            cover_image_content = cover_image.read()
        book.set_cover("cover.webp", cover_image_content)

    # 获取所有 txt 章节文件
    txt_files = glob.glob(os.path.join(book_path, '*.txt'))
    txt_files.sort(key=lambda x: int(os.path.basename(x).split('_')[0]))

    # 创建章节
    chapters = []
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            file_name = os.path.basename(file_path)
            chapter_id = file_name.split('_')[0]
            title = file_name.split('_')[1].split('.')[0]
            chapter_file = f'{chapter_id}_{title}.xhtml'

            chapter = epub.EpubHtml(title=title, file_name=chapter_file, lang='zh')
            chapter.content = f'<h2>{title}</h2><p>{content.replace(" ", "</p><p>")}</p>'
            chapter.add_link(href='styles.css', rel='stylesheet', type='text/css')

            book.add_item(chapter)
            chapters.append(chapter)

    # 设置目录
    book.toc = [epub.Section(book_name, chapters)]

    # 添加 EPUB 目录和导航
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 设置阅读顺序
    book.spine = ['nav'] + chapters

    # 写入 EPUB 文件
    epub_path = os.path.join(get_download_path(), f'{book_name}.epub')
    epub.write_epub(epub_path, book)
    print(f'✅ EPUB 生成成功: {epub_path}')


def download_image(url, save_path):
    try:
        # 发送 HTTP GET 请求
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功

        # 以二进制写入模式打开文件
        with open(save_path, 'wb') as file:
            # 分块写入文件
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"图片已保存到: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")


async def spider_book_async(book_id, max_concurrent=100):
    book_path = get_download_path() + f'/{book_id}'
    with open(book_path + '/desc.json', 'r', encoding='utf-8') as f:
        desc_json = json.load(f)
    book_pic = desc_json['book_pic']
    spider_rule = desc_json['spider_rule']
    spider_base_url = desc_json['spider_base_url']
    catalog_list = desc_json['catalog_list']

    if not os.path.exists(book_path + '/pic.webp') and book_pic is not None and book_pic.startswith('http'):
        download_image(book_pic, book_path + '/pic.webp')

    # 创建信号量来限制并发数量
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_chapter(chapter, index, total):
        _id = chapter.get('index', f'{index:05d}')
        file_name = f'{_id}_{chapter["title"]}.txt'
        file_path = f'{book_path}/{file_name.replace("/", "／")}'

        if not os.path.exists(file_path):
            if 'spider_url' in chapter and chapter['spider_url'] is not None:
                print(f'{index}/{total} {chapter["title"]} spider...')
                async with semaphore:  # 使用信号量控制并发
                    try:
                        content = await spider_content_async(spider_base_url, chapter['spider_url'], spider_rule)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f'✅ {index}/{total} {chapter["title"]} completed')
                    except Exception as e:
                        print(f'❌ {index}/{total} {chapter["title"]} failed: {str(e)}')
            else:
                print(f'{index}/{total} {chapter["title"]} skip...')

    # 创建所有任务
    tasks = []
    for index, chapter in enumerate(catalog_list, 1):
        task = asyncio.create_task(process_chapter(chapter, index, len(catalog_list)))
        tasks.append(task)

    # 等待所有任务完成
    await asyncio.gather(*tasks)


def txt_to_epub(txt_file, epub_file, title="小说标题", author="未知作者"):
    # 读取 TXT 内容
    with open(txt_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 创建 EPUB 书籍对象
    book = epub.EpubBook()
    book.set_identifier("id123456")
    book.set_title(title)
    book.set_language("zh")
    book.add_author(author)

    # 处理章节
    chapters = []
    chapter_content = []
    chapter_title = "开始"
    chapter_index = 0  # 用于文件名

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("第") and ("章" in line or "回" in line):  # 判断是否是章节标题
            # 遇到新章节，保存旧章节
            if chapter_content:
                c = epub.EpubHtml(title=chapter_title, file_name=f"chapter_{chapter_index}.xhtml", lang="zh")
                c.content = f"<h2>{chapter_title}</h2>" + "<p>" + "</p><p>".join(chapter_content) + "</p>"
                book.add_item(c)
                chapters.append(c)
                chapter_index += 1
                chapter_content = []

            # 更新章节标题
            chapter_title = line
        else:
            chapter_content.append(line)

    # 添加最后一章
    if chapter_content:
        c = epub.EpubHtml(title=chapter_title, file_name=f"chapter_{chapter_index}.xhtml", lang="zh")
        c.content = f"<h2>{chapter_title}</h2>" + "<p>" + "</p><p>".join(chapter_content) + "</p>"
        book.add_item(c)
        chapters.append(c)

    # ✅ Apple Books 兼容目录
    book.toc = [epub.Section(title, chapters)]  # 使用 epub.Section()

    # ✅ 添加导航文件
    book.add_item(epub.EpubNcx())  # EPUB 2 目录
    book.add_item(epub.EpubNav())  # EPUB 3 目录（Books 依赖此文件）

    # ✅ 设定 spine，确保章节可见
    book.spine = ["nav"] + chapters  # Apple Books 需要 "nav" 作为第一个 item

    # 写入 EPUB 文件
    epub.write_epub(epub_file, book, {})

    print(f"EPUB 生成成功: {epub_file}")
