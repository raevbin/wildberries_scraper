import scrapy
import logging
import requests
from envparse import env
from scrapy import signals
from pprint import pprint
import hashlib
from datetime import datetime
import json
from wildsearch_crawler.tools import date_for_json

logger = logging.getLogger('main')

class BaseSpider(scrapy.Spider):
    number = None

    def __init__(self, **kwargs):
        self.set_number()
        super().__init__(**kwargs)
        logger.info(f'\n\n\ninit spider:{self.name}, number: {self.number}\n')


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BaseSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def set_number(self):
        date = str(datetime.now())
        self.number = hashlib.md5(date.encode('utf-8')).hexdigest()

    def spider_opened(self, spider):
        logger.info(f'Spider opened: {spider.name}')

        pass

    def print_report(self):
        stat = json.dumps(self.crawler.stats.get_stats(),
                        indent=4,
                        sort_keys=True,
                        default=date_for_json)
        logger.info(f'''\nSpider closed: {self.name}, number:{self.number}
        stat:\n{stat}\n\n''')

    def spider_closed(self, spider, reason):
        self.print_report()




    def spider_error(self, failure, response, spider):
        logger.error(f'spider error: {failure} {response} {spider}')

    def request_dropped(self, request, spider):
        logger.error(f'request dropped: {request} {spider}')

    def errback_httpbin(self, failure):
        if failure.check(HttpError):
            response = failure.value.response
            proxy = response.meta.get('proxy')
            logger.error(f'HttpError on proxy:{proxy} url:{response.url}')

        elif failure.check(DNSLookupError):
            # this is the original request
            response = failure.value.response
            proxy = response.meta.get('proxy')
            logger.error(f'DNSLookupError on proxy:{proxy} url:{response.url}')

        elif failure.check(TimeoutError, TCPTimedOutError):
            response = failure.value.response
            proxy = response.meta.get('proxy')
            logger.error(f'TimeoutError on proxy:{proxy} url:{response.url}')

        else:
            logger.error(f'errback_httpbin {failure.raiseException}')


    def closed(self, reason):
        callback_url = getattr(self, 'callback_url', None)
        callback_params_raw = getattr(self, 'callback_params', None)
        callback_params = {
            'job_id': env('SCRAPY_JOB', default=0)
        }

        if callback_params_raw is not None:
            for element in callback_params_raw.split('&'):
                k_v = element.split('=')
                callback_params[str(k_v[0])] = k_v[1]

        if callback_url is not None:
            logger.info(f"Noticed callback_url in params, sending POST request to {callback_url}")
            requests.post(callback_url, data=callback_params)
