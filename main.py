"""
@author jeneral
@date 2025/02/18 10:53
@desc 
"""
from tool import *

if __name__ == '__main__':
    novel_id = 1012584111
    spider_url = 'https://www.22biqu.com/biqu7034/'
    cookie = 'supportwebp=true; newstatisticUUID=1729142934_858182229; fu=176397045; _csrfToken=epO91Mrp598aJ6AWsSjiriBSGsyx4SX52bwI8wMw; HMACCOUNT=0E827DE7D42F4B6B; Hm_lvt_f00f67093ce2f38f215010b699629083=1738977401; e2=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A2%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22%22%7D; e1=%7B%22l6%22%3A%22%22%2C%22l7%22%3A%22%22%2C%22l1%22%3A3%2C%22l3%22%3A%22%22%2C%22pid%22%3A%22qd_p_qidian%22%2C%22eid%22%3A%22qd_A17%22%7D; _gid=GA1.2.1032812091.1739414833; supportWebp=true; se_ref=; traffic_utm_referer=https%3A//www.bing.com/; _gat_gtag_UA_199934072_2=1; Hm_lpvt_f00f67093ce2f38f215010b699629083=1739435973; _ga=GA1.1.530203218.1729129077; _ga_PFYW0QLV3P=GS1.1.1739435970.12.1.1739435973.0.0.0; _ga_FZMMH98S83=GS1.1.1739435970.12.1.1739435973.0.0.0; w_tsfp=ltvuV0MF2utBvS0Q6qPtl02uFjgjcjs4h0wpEaR0f5thQLErU5mG2IJ5uMv3MHzY5cxnvd7DsZoyJTLYCJI3dwMTRp6UIIwRhQ6ZldAm2IxCUEY0FJ/UWFQeIrgj7mFAeHhCNxS00jA8eIUd379yilkMsyN1zap3TO14fstJ019E6KDQmI5uDW3HlFWQRzaLbjcMcuqPr6g18L5a5TuO5Q+pKQkmBrJA2E2XhC4YXXh25RW5Jr9VMxz+ccioSqA='
    write_desc(novel_id, spider_url, cookie)
    spider_book(novel_id)
    write_epub(novel_id)
