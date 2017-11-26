# -*- coding: utf-8 -*-
import scrapy
from iphone.items import DBItem, ImgItem
import re


class IphonespiderSpider(scrapy.Spider):
    name = 'iphone'
    allowed_domains = ['theiphonewiki.com']
    start_urls = ['https://www.theiphonewiki.com/wiki/List_of_iPhones']

    def parse(self, response):
        db = DBItem()
        img = ImgItem()

        image_urls = response.xpath('//*[@id="mw-content-text"]/div/div/a/img')
        names = response.xpath('//*[@id="mw-content-text"]')
        cpus = response.xpath('//*[@id="mw-content-text"]/ul/li[6]/ul/li[2]')
        cameras = response.xpath('//*[@id="mw-content-text"]/ul/li[3]/ul')

        for index in range(len(cpus)):
            img['image_urls'] = "https://www.theiphonewiki.com" + image_urls[index].xpath('@src').extract_first()
            db['image_url'] = self.settings.get('IMAGES_STORE', None) + image_urls[index].xpath('@src').extract_first().split('/')[-1]

            db['name'] = names.css('span a::text').extract()[index]

            cpu_text = cpus[index].css('li::text').extract()
            for text in cpu_text:
                r = re.search("[A-Z][0-9]+", text)
                if r:
                    db['cpu'] = r.group(0)

            db['internal_name'] = response.xpath('//*[@id="mw-content-text"]/ul/li[8]').css(
                'li::text').extract()[index].partition(':')[2]
            db['ram'] = response.xpath('//*[@id="mw-content-text"]/ul/li[9]').css(
                'li::text').extract()[index].partition(':')[2]
            db['storage'] = response.xpath('//*[@id="mw-content-text"]/ul/li[10]').css(
                'li::text').extract()[index].partition(':')[2]

            for text in response.xpath('//*[@id="mw-content-text"]/ul/li[4]')[index].css('li::text').extract():
                r = re.search("[0-9.G]+", text)
                if r:
                    db['cellular'] = r.group(0)

            for text in cameras[index].css('li::text').extract():
                if text.find('Front:') > 0:
                    db['front_camera'] = text.partition(':')[2]
                elif text.find('Rear:') > 0:
                    db['rear_camera'] = text.partition(':')[2]

            db['battery'] = response.xpath('//*[@id="mw-content-text"]/ul/li[1]/ul/li[1]/text()').extract()[index].partition(':')[2]

            yield img
            yield db

