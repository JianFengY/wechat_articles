# wechat_articles
爬取搜狗微信搜索的文章

`proxy_pool`为代理池部分

代理池使用flask+redis维护，也可以独立使用：
- 执行`run.py`
- 访问`http://localhost:5000/get`获取一个可用代理

`articles_spider`为爬虫部分，使用requests+pyquery实现

爬取指定关键字的搜索结果页面共100页

爬取结果存储在MongoDB
