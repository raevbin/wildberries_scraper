from scrapy import signals
from w3lib.http import basic_auth_header
from fake_useragent import UserAgent
from .tools import ProxyRotator
from .settings import DOWNLOAD_TIMEAUT
import logging
logger = logging.getLogger('main')
connect_log = logging.getLogger('connect')

user_agent = UserAgent()

proxy = ProxyRotator()


class CustomProxyMiddleware(object):
    def process_request(self, request, spider):

        retry_times = request.meta.get('retry_times')
        if retry_times:
            old_proxy = request.meta.get('proxy')
            target_domen = request.meta.get('download_slot')
            proxy.delete(old_proxy,
                f'Connection refused: proxy deleted, target {target_domen}' )
            count_proxy = len(proxy.get_proxy_list())
            mess = f'Connection refused: proxy {old_proxy} deleted, \
                    target {target_domen} !!! total servers left {count_proxy}'
            connect_log.error(mess)


        proxy_addr = proxy.next()
        if proxy_addr:
            logger.info(f'use proxy: { proxy_addr}')
            request.meta['proxy'] = proxy_addr
        else:
            logger.info(f'>>> !!! there are no more servers left. \
                                                    using primary address !!!')

        if DOWNLOAD_TIMEAUT:
            request.meta['download_timeout'] = DOWNLOAD_TIMEAUT

        request.headers['User-Agent'] = user_agent.random


class WildsearchCrawlerSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):

        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        pass
        # logger.info(f'WildsearchCrawlerSpiderMiddleware Spider opened: {spider.name}')


class WildsearchCrawlerDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):

        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        pass
