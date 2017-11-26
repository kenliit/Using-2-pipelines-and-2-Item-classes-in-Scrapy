# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class DBItem(Item):
    name = Field()
    cpu = Field()
    internal_name = Field()
    cellular = Field()
    ram = Field()
    storage = Field()
    front_camera = Field()
    rear_camera = Field()
    battery = Field()
    image_url = Field()


class ImgItem(Item):
    image_urls = Field()
    images = Field()


