# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem
from iphone.items import DBItem, ImgItem

import logging
import pprint

from pymysql.cursors import DictCursor

from pymysql import OperationalError
from pymysql.constants.CR import CR_SERVER_GONE_ERROR,  CR_SERVER_LOST, CR_CONNECTION_ERROR
from twisted.internet import defer
from twisted.enterprise import adbapi

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class IphonePipeline(object):

    stats_name = 'iphone_pipeline'

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.stats = crawler.stats
        self.settings = crawler.settings
        db_args = {
            'host': self.settings.get('MYSQL_HOST', 'localhost'),
            'port': self.settings.get('MYSQL_PORT', 3306),
            'user': self.settings.get('MYSQL_USER', None),
            'password': self.settings.get('MYSQL_PASSWORD', ''),
            'db': self.settings.get('MYSQL_DB', None),
            'charset': 'utf8',
            'cursorclass': DictCursor,
            'cp_reconnect': True,
        }
        self.retries = self.settings.get('MYSQL_RETRIES', 3)
        self.close_on_error = self.settings.get('MYSQL_CLOSE_ON_ERROR', True)
        self.upsert = self.settings.get('MYSQL_UPSERT', False)
        self.table = self.settings.get('MYSQL_TABLE', None)
        self.db = adbapi.ConnectionPool('pymysql', **db_args)

    def close_spider(self, spider):
        self.db.close()

    @staticmethod
    def preprocess_item(item):
        # put something here needed to be handle before the process
        return item

    def postprocess_item(self, *args):
        # Can be useful if you need to update query tables depends of mysql query result
        pass

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        if not isinstance(item, DBItem):
            return item

        print("I am here...")

        retries = self.retries
        status = False
        while retries:
            try:
                item = self.preprocess_item(item)
                sql, data = self._generate_sql(item)
                self.db.runQuery(sql, data)
            except OperationalError as e:
                if e.args[0] in (
                        CR_SERVER_GONE_ERROR,
                        CR_SERVER_LOST,
                        CR_CONNECTION_ERROR,
                ):
                    retries -= 1
                    logger.info('%s %s attempts to reconnect left', e, retries)
                    self.stats.inc_value('{}/reconnects'.format(self.stats_name))
                    continue
                logger.exception('%s', pprint.pformat(item))
                self.stats.inc_value('{}/errors'.format(self.stats_name))
            except Exception:
                logger.exception('%s', pprint.pformat(item))
                self.stats.inc_value('{}/errors'.format(self.stats_name))
            else:
                status = True  # executed without errors
            break
        else:
            if self.close_on_error:  # Close spider if connection error happened and MYSQL_CLOSE_ON_ERROR = True
                spider.crawler.engine.close_spider(spider, '{}_fatal_error'.format(self.stats_name))
        self.postprocess_item(item, status)
        yield item

    def _generate_sql(self, data):
        columns = lambda d: ', '.join(['`{}`'.format(k) for k in d])
        values = lambda d: [v for v in d.values()]
        placeholders = lambda d: ', '.join(['%s'] * len(d))
        if self.upsert:
            sql_template = 'INSERT INTO `{}` ( {} ) VALUES ( {} ) ON DUPLICATE KEY UPDATE {}'
            on_duplicate_placeholders = lambda d: ', '.join(['`{}` = %s'.format(k) for k in d])
            return (
                sql_template.format(
                    self.table, columns(data),
                    placeholders(data), on_duplicate_placeholders(data)
                ),
                values(data) + values(data)
            )
        else:
            sql_template = 'INSERT INTO `{}` ( {} ) VALUES ( {} )'
            return (
                sql_template.format(self.table, columns(data), placeholders(data)),
                values(data)
            )


class MyImagesPipeline(ImagesPipeline):

    def image_key(self, url):
        image_guid = url.split('/')[-1]
        return 'full/%s' % (image_guid)

    def get_media_requests(self, item, info):
        if not isinstance(item, ImgItem):
            return item
        yield scrapy.Request(item['image_urls'])

    def item_completed(self, results, item, info):
        return item
