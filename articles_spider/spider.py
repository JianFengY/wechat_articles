"""
Created on 2018/3/1
@Author: Jeff Yang
"""
from urllib.parse import urlencode
import requests
from  requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import pymongo
# from multiprocessing import Pool
# from multiprocessing.dummy import Pool as TheadPool

from articles_spider.config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

base_url = 'http://weixin.sogou.com/weixin?'

# 注意cookie是有时限的，失效以后页面会有‘Auth Result: 无效用户’的提示
headers = {
    'Cookie': 'xxxxxxxxxxxxxx',  # 你的cookies
    'Host': 'weixin.sogou.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
}

proxy = None  # 代理的全局变量，访问302了才开始使用代理


def get_proxy():
    """获取代理"""
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html(url, count=1):
    """获取页面源码"""
    print('Crawling url: ', url)
    print('Tring count: ', count)
    global proxy
    if count >= MAX_COUNT:
        print('Tried too many times!')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers,
                                    proxies=proxies)  # allow_redirects=False不让requests自动处理302跳转
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:  # 连续访问20页ip就会被封，状态码为302
            proxy = get_proxy()
            if proxy:
                print('Using proxy:', proxy)
                # count += 1
                # return get_html(url, count)
                return get_html(url)  # 次数不加，因为免费代理可能有很多人用被封掉，所以可能要多次尝试
            else:
                print('Fail to get proxy')
                return None
    except ConnectionError as e:
        print('Error occurred: ', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)


def get_index(page):
    """构造url调用get_html()获取页面信息"""
    data = {
        'query': KEYWORD,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html


def parse_index(html):
    """使用pyquery解析索引页"""
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()  # 页面所有文章的超链接<a>标签
    for item in items:
        yield item.attr('href')


def get_detail(url):
    """获取正文内容"""
    try:
        response = requests.get(url)  # 微信链接没有封IP等反爬措施，可以直接获取
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def parse_detail(html):
    """解析文章内容"""
    doc = pq(html)
    title = doc('.rich_media_title').text()
    content = doc('.rich_media_content').text()
    date = doc('#post-date').text()
    nickname = doc('#js_profile_qrcode > div > strong').text()
    wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
    return {
        'title': title,
        'content': content,
        'date': date,
        'nickname': nickname,
        'wechat': wechat,
    }


def save_to_mongo(data):
    """保存到MongoDB"""
    if db['articles'].update({'title': data['title']}, {'$set': data}, True):  # 如果文章不存在就插入，存在就更新
        print('Save to Mongo: ', data['title'])
    else:
        print('Save to Mongo failed: ', data['title'])


def main():
    # pool = Pool()
    # htmls = pool.map(get_index,[page for page in range(1, 101)])
    # print(page, ': ', html)
    # for html in htmls:
    for page in range(1, 101):
        html = get_index(page)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    print(article_data)
                    if article_data:
                        save_to_mongo(article_data)


if __name__ == '__main__':
    main()
    print("Done!")
