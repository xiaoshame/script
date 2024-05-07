# -*- coding: utf-8 -*-
import os

from bookspider.items import BookSpiderItem
import scrapy
import urllib
import re
import json
import subprocess
from functools import partial
import os.path
subprocess.Popen = partial(subprocess.Popen, encoding="utf-8")
import execjs


class BeitaiSpider(scrapy.Spider):
    name = 'beitai'
    allowed_domains = ['beitai.cc']
    base_url = "https://beitai.cc"
    start_urls = ["https://beitai.cc/%E5%AF%BC%E8%88%AA"]

    def parse(self, response):
        authors_table = response.xpath("//article[@class='markdown-body']/table")
        authors_ul = response.xpath("//article[@class='markdown-body']/ul")
        for author in authors_table:
            author_name = ""
            author_url = ""
            if len(author.xpath("thead/tr/th/a/text()").extract()) == 0 or len(author.xpath("thead/tr/th/a/@href").extract()) == 0:
                continue
            else:
                author_name = author.xpath("thead/tr/th/a/text()").extract()[0]
                author_url = author.xpath("thead/tr/th/a/@href").extract()[0]
                author_url = author_url.replace("..","")
                yield scrapy.Request(self.base_url + author_url,meta={"authorName":author_name},callback=self.getBooks)
            
            authors_body = author.xpath("tbody/tr")
            for author_body in authors_body:
                author_body_name = ""
                author_body_url = ""
                if len(author_body.xpath("td/a/text()").extract()) == 0 or len(author_body.xpath("td/a/@href").extract()) == 0:
                    continue
                else:
                    author_body_name = author_body.xpath("td/a/text()").extract()[0]
                    author_body_url = author_body.xpath("td/a/@href").extract()[0]
                    author_body_url = author_body_url.replace("..","")
                    yield scrapy.Request(self.base_url +author_body_url,meta={"authorName":author_body_name},callback=self.getBooks)

        for author in authors_ul:
            author_name = ""
            author_url = ""
            if len(author.xpath("li/a/text()").extract()) == 0 or len(author.xpath("li/a/@href").extract()) == 0:
                continue
            else:
                author_name = author.xpath("li/a/text()").extract()[0]
                author_url = author.xpath("li/a/@href").extract()[0]
                author_url = author_url.replace("..","")
                yield scrapy.Request(self.base_url + author_url,meta={"authorName":author_name},callback=self.getBooks)


    def getBooks(self,response):
        # response.encoding = "gbk"

        author_name = response.meta["authorName"]

        books = response.xpath("//article[@class='markdown-body']/table/tbody/tr")
        for book in books:
            if len(book.xpath("td[1]/text()").extract()) == 0 or len(book.xpath("td[6]/a/@href").extract()) == 0:
                continue
            else:
                bookName = book.xpath("td[1]/text()").extract()[0]
                download_url = book.xpath("td[6]/a/@href").extract()[0]
                download_url = download_url.replace("..","")
                yield scrapy.Request(self.base_url + download_url,meta={"authorName":author_name,"bookName":bookName},callback=self.getContent)

    def getContent(self,response):
        author = response.meta["authorName"]
        bookName = response.meta["bookName"]
        dirpath = './book/网络/'
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filepath = os.path.join(dirpath, author + "_" + bookName + ".rar")
        with open(filepath, "wb") as file:
            file.write(response.body)
            file.close()

