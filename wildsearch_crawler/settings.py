# -*- coding: utf-8 -*-
import logging
from scrapy.utils.log import configure_logging
import inspect
import os
import pathlib
from selenium.webdriver.remote.remote_connection import LOGGER
from urllib3.connectionpool import log as urllibLogger
def set_level_logging(level):
    urllibLogger.setLevel(level)
    LOGGER.setLevel(level)



# from shutil import which
#
# SELENIUM_DRIVER_NAME = 'chrome'
# # SELENIUM_DRIVER_EXECUTABLE_PATH = which('geckodriver')
# SELENIUM_COMMAND_EXECUTOR = 'http://selenoid:4444/wd/hub'
# SELENIUM_DRIVER_ARGUMENTS=['--headless']

SELENOID_HUB = 'http://selenoid:4444/wd/hub'
SELENOID_STATUS_URL =  'http://selenoid:4444/status'


FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
PROJECTPATH = pathlib.Path(os.path.dirname(os.path.abspath(FILENAME)))
ROOTPATH = PROJECTPATH.parent



ERROR_TRACE_LEVEL = 10

# ====================== DABASE ======================


WS_DB_ENGINE = 'mysql+mysqldb://root:root@db:3306/wildsearch?charset=utf8'
OZ_DB_ENGINE = 'mysql+mysqldb://root:root@db:3306/ozon?charset=utf8'


# ====================== PROXY ======================
SCYLLA_URL = 'http://scylla:8899/api/v1/proxies'

PROXY_LIST_CSV = f'{ROOTPATH}/proxy_list.csv'

PROXY_FILTER = {
    'protocol': 'socks', # https, http
}

PROXY_POSTPONE_ON = 120 # minutes

UPLOAD_NEW_PROXIES_IF_LESS_THAN = 3
PROXY_SOURSE_DEFAULT = 'csv'
PROXY_MODE_DEFAULT = 'reload'

USE_PROXY_FOR_OZ_QTY = True

# ====================== OZ_QTY =====================

OZ_QTY_PORTION = 10
OZ_QTY_COUNT_PORTION = 2

CHROME_ARGS = [
    'start-maximized',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-browser-side-navigation',
    '--disable-infobars',
    # '--no-sandbox',
    'enable-automation'
]

# ====================== DELAY ======================
# DOWNLOAD_DELAY = 2
DOWNLOAD_TIMEAUT = 5

# https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 0
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 300
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True




# ====================== LOGGER ======================

configure_logging(install_root_handler=False)
logging.getLogger('scrapy').propagate = False
LOG_ENABLED = False


set_level_logging(logging.DEBUG)


logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {
                'format': "###{lineno} {module} {funcName} {message}",
                'style': "{",
            },
            'detailed': {
                'format':"{levelname} {asctime} {module} {funcName} {lineno} {process}/{thread} {message} " ,
                'style': "{",
            },
            'message':{
                'format':"#{asctime} #{message}",
                'style': "{",
            }

        },
        'handlers': {
            'console': {
                'class': "logging.StreamHandler",
                'formatter': "simple",
                'level': "INFO",
            },
            'main': {
                'class': "logging.handlers.RotatingFileHandler",
                'filename': f"{ROOTPATH}/logs/main.log",
                'formatter': "detailed",
                'mode': "a",
                'maxBytes': 5*1024*1024,
                'backupCount': 5,
                'level': "INFO",
            },
            'connect': {
                'class': "logging.handlers.RotatingFileHandler",
                'filename': f"{ROOTPATH}/logs/connect.log",
                'formatter': "message",
                'mode': "a",
                'maxBytes': 5*1024*1024,
                'backupCount': 5,
                'level': "INFO",
            },

        },
        'loggers': {

            'main': {
                'handlers': ["main"]
            },
            'connect': {
                'handlers': ["main", "connect"]
            }

        },
        # 'root': {
        #     'level': "DEBUG",
        #     'handlers': [
        #             "console",
        #             # "errors"
        #     ]
        # },
})




BOT_NAME = 'wildsearch_crawler'

SPIDER_MODULES = ['wildsearch_crawler.spiders']
NEWSPIDER_MODULE = 'wildsearch_crawler.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'PostmanRuntime/7.21.0'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html


# ====================== SPLASH ======================

SPLASH_URL = 'http://splash:8050'

DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'

SPLASH_COOKIES_DEBUG = True

# =============================================================================

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
    'wildsearch_crawler.middlewares.WildsearchCrawlerSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'wildsearch_crawler.middlewares.CustomRetryMiddleware': 200,
    'wildsearch_crawler.middlewares.CustomProxyMiddleware': 350,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    # 'scrapy_selenium.SeleniumMiddleware': 800,
    'wildsearch_crawler.middlewares.WildsearchCrawlerDownloaderMiddleware': 543,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'wildsearch_crawler.pipelines.WildsearchCrawlerPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
