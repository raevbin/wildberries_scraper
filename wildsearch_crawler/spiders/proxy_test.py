import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
import logging
from scrapy import signals
import time
from wildsearch_crawler.tools import ProxyRotator, ProxyLoader
from wildsearch_crawler.settings import PROXY_LIST_CSV, PROXY_FILTER, ERROR_TRACE_LEVEL
from wildsearch_crawler.settings import PROXY_SOURSE_DEFAULT, PROXY_MODE_DEFAULT
from pprint import pprint
import traceback
from .base_spider import BaseSpider



logger = logging.getLogger('main')


class ProxyTestSpider(BaseSpider):

    name = 'proxy_test'
    allowed_domains = ['mybrowserinfo.com']



    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ProxyTestSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.proxy_test_closed, signal=signals.spider_closed)
        crawler.signals.connect(spider.request_dropped, signal=signals.request_dropped)
        return spider


    def start_requests(self):
        try:
            logger.info('------- ProxyTestSpider start_requests -------------')
            source = getattr(self, 'source', PROXY_SOURSE_DEFAULT) #   csv , scylla, none
            mode = getattr(self, 'mode', PROXY_MODE_DEFAULT) # reload, reset, current
            protocol = getattr(self, 'protocol', PROXY_FILTER.get('protocol')) # https, socks, all....
            group = getattr(self, 'group', PROXY_FILTER.get('group'))
            use_postponed = getattr(self, 'use_postponed', False)

            loader = ProxyLoader()

            if mode != 'current':
                if source == 'csv':
                    loader.from_csv(PROXY_LIST_CSV, group if group else 'new')
                elif source == 'scylla':
                    loader.from_scylla()

            proxy = ProxyRotator()

            if protocol:
                PROXY_FILTER['protocol'] = protocol
            if group:
                PROXY_FILTER['group'] = group

            if use_postponed:
                PROXY_FILTER['use_postponed'] = True

            if mode == 'reset':
                proxy.reset()

            if mode != 'current':
                proxy.reload(**PROXY_FILTER)

            count = len(proxy.get_proxy_list())
            # print('get_proxy_list', proxy.get_proxy_list())


            for i in range(count):
                logger.info(f'current Request  N {i}')
                yield scrapy.Request('https://mybrowserinfo.com/',
                        self.parse_item,
                        errback=self.errback_httpbin,
                        dont_filter=True)

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise


    def parse_item(self, response):

        proxy = response.meta.get('proxy')
        ip = response.css('#main h1::text').get()
        agent = response.css('#main h2 span::text')[1].get()
        logger.info(f'response:\nfrom proxy {proxy} {ip}, user-agent: {agent}')

    def proxy_test_closed(self, spider):
        logger.info(f'count proxy : {len(ProxyRotator().get_proxy_list())}')
