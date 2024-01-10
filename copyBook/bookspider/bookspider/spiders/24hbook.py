# -*- coding: utf-8 -*-
import os

from bookspider.items import BookSpiderItem
import scrapy
import urllib
import re
import json

class ShuqiSpider(scrapy.Spider):
    name = '24book'
    allowed_domains = ['24hbook.com','router.24hbook.com']
    start_urls = ["https://24hbook.com/search?query=%E5%B0%8F%E8%AF%B4&limit=20&offset=0"]
    download_base_url = "https://router.24hbook.com:3721/ipfs/{}?filename={}.{}"
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:1081"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:1081"
    # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"

    def parse(self, response):
        data = json.loads(response.text)
        if data.get('offset') < data.get('total'):
            url = "https://24hbook.com/search?query=%E5%B0%8F%E8%AF%B4&limit=20&offset={}".format(data.get('offset') + 20)
            yield scrapy.Request(url,callback=self.parse)
        parsed_url = urllib.parse.urlparse(response.url)
        categoryName = urllib.parse.parse_qs(parsed_url.query)["query"][0]
        for book in data.get('books'):
            title = book.get('title')
            author = book.get('author')
            extension = book.get('extension')
            language = book.get('language')
            dirpath = './book/' + categoryName
            filepath = os.path.join(dirpath, author + "_" + title + "." + extension)
            bookUrl = self.download_base_url.format(book.get('ipfs_cid'),title,extension)
            if language == "Chinese" and not os.path.exists(filepath):
                yield scrapy.Request(bookUrl,meta={
                                            "categoryName":categoryName,
                                            'bookName':title,
                                            'author':author,
                                            'extension':extension,
                                            },callback=self.getContent)

    def getContent(self,response):
        categoryName = response.meta["categoryName"]
        bookName = response.meta["bookName"]
        extension = response.meta["extension"]
        author = response.meta["author"]
        dirpath = './book/' + categoryName
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filepath = os.path.join(dirpath, author + "_" + bookName + "." + extension)
        with open(filepath, "wb") as file:
            file.write(response.body)
            file.close()