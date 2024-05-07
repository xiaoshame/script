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


class ShuqiSpider(scrapy.Spider):
    name = 'shuqi'
    allowed_domains = ['shuqi.com','c13.shuqireader.com']
    base_url = "https://shuqi.com"
    start_urls = ["https://shuqi.com/store?&sz=male"]

    def parse(self, response):
        categorys = response.xpath("//div[@class='selectarea clear'][2]/ul/li")

        for category in categorys:
            categoryUrl = category.xpath("a/@href").extract()[0]
            categoryName = category.xpath("a/text()").extract()[0]
            # print(self.start_urls[0] + categoryUrl)
            # while self.getNext(categoryUrl) != -1:
            #     print(categoryUrl)
            #     categoryUrl = self.getNext(categoryUrl)
            # yield scrapy.Request(self.start_urls + categoryUrl,meta={"categoryName":categoryName},callback=self.getNext)
            yield scrapy.Request(self.base_url + categoryUrl,meta={"categoryName":categoryName},callback=self.getNext)
        # yield scrapy.Request(self.base_url+ "/book/8738007.html",meta={"categoryName":"测试"},callback=self.getBooks)



    def getNext(self,response):
        # response.encoding = "gbk"

        categoryName = response.meta["categoryName"]

        nextUrl = ""
        nextUrl_result = response.xpath("//div[@class='comp-web-pages']/span[8]/a/@href").extract()
        if len(nextUrl_result) != 0:
            nextUrl = self.base_url + nextUrl_result[0]
            yield scrapy.Request(nextUrl,meta={"categoryName":categoryName},callback=self.getNext)

        urls = response.xpath("//ul[@class='store-ul clear']//li")
        for url in urls:
            bookUrl = self.base_url + url.xpath('a/@href').extract()[0]
            yield scrapy.Request(bookUrl,meta={"categoryName":categoryName},callback=self.getBooks)


    def getBooks(self,response):
        categoryName = response.meta["categoryName"]

        bookName = ""
        bookName_result = response.xpath("//div[@class='infoarea']/div[@class='view']/p[@class='bookTitle']/span[1]/text()").extract()
        if len(bookName_result) == 0:
            return 
        else:
            bookName = bookName_result[0]
        bookUrl = self.base_url + response.xpath("//div[@class='infoarea']/div[@class='view']/ul[@class='operates clear']/li[2]/a/@href").extract()[0]
        author = response.xpath("//div[@class='infoarea']/div[@class='view']/p[@class='bookTitle']/span[2]/a/text()").extract()[0]
        intro_result = response.xpath("//div[@class='infoarea']/div[@class='view']/p[@class='bookDesc']/text()").extract()
        intro = ""
        if len(intro_result):
            intro = intro_result[0]
        imgUrl = response.xpath("//div[@class='infoarea']/div[@class='view']/img/@src").extract()[0]

        filename = bookName + '.jpg'
        dirpath = './cover'
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filepath = os.path.join(dirpath, filename)
        urllib.request.urlretrieve(imgUrl, filepath)

        cover = 'cover/' + filename
        # print(bookName,':',bookUrl)
        # print("------------------------------------------------------")
        yield scrapy.Request(bookUrl,meta={"categoryName":categoryName,
                                           'bookName':bookName,
                                           'bookUrl':bookUrl,
                                           'author':author,
                                           'intro':intro,
                                           'cover':cover
                                           },callback=self.getChapter)


    def getChapter(self,response):
        categoryName = response.meta["categoryName"]
        bookName = response.meta["bookName"]
        bookUrl = response.meta["bookUrl"]
        author = response.meta["author"]
        intro = response.meta["intro"]
        cover = response.meta["cover"]


        chapters = response.xpath("//table//td")
        number = 0

        for chapter in chapters:
            number += 1
            chapterName = chapter.xpath("a/text()").extract()[0]
            chapterUrl = self.base_url + chapter.xpath("a/@href").extract()[0]
            # print(categoryName)
            # print('          -----------',bookName,':',bookUrl)
            # print('                         --------------',chapterName,':',chapterUrl)
            # print("-------------------------------------------------------------------")
            yield scrapy.Request(chapterUrl,meta={
                'categoryName':categoryName,
                'bookName': bookName,
                'bookUrl': bookUrl,
                'chapterName': chapterName,
                'chapterUrl': chapterUrl,
                'author': author,
                'intro': intro,
                'cover': cover,
                'number':number
            },callback=self.getContent)

    def getContent(self,response):
        categoryName = response.meta["categoryName"]
        bookName = response.meta["bookName"]
        bookUrl = response.meta["bookUrl"]
        chapterName = response.meta["chapterName"]
        chapterUrl = response.meta["chapterUrl"]
        author = response.meta["author"]
        intro = response.meta["intro"]
        cover = response.meta["cover"]
        number = response.meta["number"]
        
        cid = re.search(r'cid=(\d+)',response.url).group(1)
        params = re.search(r'(\?bookId=[^,]+chapterId=' + cid + '[^,]+num=[^,]+)&quot;',response.text)
        if(params is not None):
            params = params[1]
            prefix = re.search(r'freeContUrlPrefix[^,]+;([^,]+)&quot;',response.text).group(1)
            if(prefix and len(prefix) > 0 and len(params)):
                chapterUrl = prefix + params
                chapterUrl = chapterUrl.replace("amp;", '')
                yield scrapy.Request(chapterUrl,meta={
                        'categoryName':categoryName,
                        'bookName': bookName,
                        'bookUrl': bookUrl,
                        'chapterName': chapterName,
                        'chapterUrl': chapterUrl,
                        'author': author,
                        'intro': intro,
                        'cover': cover,
                        'number':number
                    },callback=self.getRealContent)
        
    def getRealContent(self,response):
        categoryName = response.meta["categoryName"]
        bookName = response.meta["bookName"]
        bookUrl = response.meta["bookUrl"]
        chapterName = response.meta["chapterName"]
        chapterUrl = response.meta["chapterUrl"]
        author = response.meta["author"]
        intro = response.meta["intro"]
        cover = response.meta["cover"]
        number = response.meta["number"]

        data = json.loads(response.text)
        if data.get('state') == "200":
            encrypt_data = data.get('ChapterContent')
            chapterContent = self.decode(encrypt_data)
            chapterContent = chapterContent.replace(u'\u3000', '')
            # chapterContent = chapterContent.replace('<br/>','\n')
            
            item = BookSpiderItem()
            item["categoryName"] = categoryName
            item["bookName"] = bookName
            item["bookUrl"] = bookUrl
            item["chapterName"] = chapterName
            item["chapterUrl"] = chapterUrl
            item["chapterContent"] = chapterContent
            item["author"] = author
            item["intro"] = intro
            item["cover"] = cover
            item["number"] = number

            return item
    
    def decode(self,data):
        path = os.path.split(os.path.realpath(__file__))[0] + '/shuqi.js'
        with open(path, 'r', encoding='UTF-8') as f:
            js_code = f.read()
            context = execjs.compile(js_code)
            result = context.call("decodeCont", data)
            return result

