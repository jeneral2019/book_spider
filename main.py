"""
@author jeneral
@date 2025/02/18 10:53
@desc 
"""
from tool import *

if __name__ == '__main__':
    novel_id = 1035035309
    cookie = 'supportwebp=true; _gid=GA1.2.195804877.1743772511; supportWebp=true; traffic_search_engine=; _csrfToken=NNRqsCEC3yidUc4BOyqKWKHVsK3kYIL4blbaKXyq; newstatisticUUID=1743907582_1225967712; fu=1606796373; Hm_lvt_f00f67093ce2f38f215010b699629083=1743486831,1743772509,1743839211,1743907582; HMACCOUNT=7A71F7CA3E240AF9; _gat_gtag_UA_199934072_2=1; e1=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A2%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22%22%7D; e2=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A2%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22%22%7D; traffic_utm_referer=https%3A//cn.bing.com/; Hm_lpvt_f00f67093ce2f38f215010b699629083=1743907613; _ga_FZMMH98S83=GS1.1.1743907582.9.1.1743907612.0.0.0; _ga=GA1.1.463861789.1743486831; _ga_PFYW0QLV3P=GS1.1.1743907582.9.1.1743907612.0.0.0; w_tsfp=ltvuV0MF2utBvS0Q7anglEyoFT0lcj04h0wpEaR0f5thQLErU5mB0o96uc30NXbc4sxnvd7DsZoyJTLYCJI3dwNFRcTCIIgY3VmTktItjY8QCRhnQpLUXF4ccOkk7zlOdXhCNxS00jA8eIUd379yilkMsyN1zap3TO14fstJ019E6KDQmI5uDW3HlFWQRzaLbjcMcuqPr6g18L5a5W7V7Fz/LApxVe4X1kOb0CgYXCsmsxK9fe1ZNUivd5uuSqA='
    spider_url = 'https://www.22biqu.com/biqu43756/'
    write_desc(novel_id, spider_url, cookie)
    asyncio.run(spider_book_async(novel_id))
    write_epub(novel_id)
