import scrapy
from scrapy_splash import SplashRequest
import logging
from pprint import pprint
from urllib.parse import urlencode

logger = logging.getLogger('main')

lua_script = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(2))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""
delete_items = """
function main(splash)
    assert(splash:go(splash.args.url))
    splash:wait(2)
    local title = splash:evaljs("$('.btn-withDotted-cross.j-basket-item-del').click()")
    return {title=title}
end
"""




class MySpider(scrapy.Spider):

    name = 'test_splash'
    start_urls = [
                "https://www.wildberries.ru/catalog/zhenshchinam/odezhda/bluzki-i-rubashki"
                ]

    def start_requests(self):
        print('start_requests >>>  ')
#
        for url in self.start_urls:
            print(f'parse url >> {url}')
            yield SplashRequest(url, self.parse,
                                    # args={'wait': 10},
                                    # endpoint='render.json',
                                    endpoint='execute',
                                    session_id=1,
                                    # headers=response.data['headers'],
                                    cache_args=['lua_source'],
                                    args={'lua_source': lua_script,
                                            'wait': 2},
                                    # headers={'X-My-Header': 'value'},
                                    )

    def parse_item(self, response):
        logger.info('\n\n\n\n')
        logger.info(response.text)

        # item_list = response.css('.item .j-b-basket-item .first')
        # logger.info(f' BOND  {response.css(".bond::text").get()}')
        # logger.info(f' EMPTY {response.css(".i-empty-basket::text").get()}')

        # logger.info(f'--==== parse_item ===== {len(item_list)}')
        # logger.info(f'{response.meta}')
        # #
        # for el in response.cookiejar:
        #     logger.info(f'{el}')
        #
        # logger.info('\n\n\n\n')

    def add_to_basket(self, response):
        logger.info(f'add_to_basket ===== {response.data["headers"]}')

    def parse(self, response):
        logger.info('\n\n\n\n')
        logger.info(response.css('title::text').get())
        # logger.info(f'headers ===== {response.data["headers"]}')


        list_item = [
            # 'https://www.wildberries.ru/catalog/8944425/detail.aspx',
            # 'https://www.wildberries.ru/catalog/9219814/detail.aspx'
        ]

        # https://lk.wildberries.ru/product/addtobasket

        # referer: https://www.wildberries.ru/catalog/8944425/detail.aspx?targetUrl=GP
        # referer: https://www.wildberries.ru/catalog/9219814/detail.aspx?targetUrl=GP


        # urlencode(a, doseq=True)

        param_list = [
            {'cod1S': 8944425,
            'characteristicId': 30033149,
            'quantity': 1,
            'isCredit': 'false',
            'rowId': 0,
            'openTime': '30/03/2020 23:28:50',
            'sizeName': 34,
            'priceWithCouponAndDiscount': 1750,
            'targetUrl': 'GP',
            'targetCode': 0,
            'source': 'BigCard'},

            {'cod1S': 9219814,
            'characteristicId': 30790714,
            'quantity': 1,
            'isCredit': 'false',
            'rowId': 0,
            'openTime': '30/03/2020 23:28:50',
            'sizeName': 36,
            'priceWithCouponAndDiscount': 1750,
            'targetUrl': 'GP',
            'targetCode': 0,
            'source': 'BigCard'}

        ]

        headers = [
            {'name': 'referer',
             'value': 'https://www.wildberries.ru/catalog/8944425/detail.aspx?targetUrl=GP'
             },
             {'name': 'referer',
              'value': 'https://www.wildberries.ru/catalog/9219814/detail.aspx?targetUrl=GP'
              },
        ]

        for i in range(2):
            # print(f'parse url >> {url}')
            yield SplashRequest('https://lk.wildberries.ru/product/addtobasket',
                                    self.add_to_basket,
                                    endpoint='execute',
                                    session_id=1,
                                    # headers=response.data['headers'],
                                    headers=[headers[i]],
                                    cache_args=['lua_source'],
                                    args={'lua_source': lua_script,
                                    'wait': 2,
                                    'http_method': 'POST',
                                    'body': urlencode(param_list[i], doseq=True)},
                                    )


        yield SplashRequest( 'https://lk.wildberries.ru/basket',
                                self.parse_item,
                                endpoint='execute',
                                session_id=1,
                                cache_args=['lua_source'],
                                args={'lua_source': lua_script,
                                'wait': 2,
                                },
                                )
        yield SplashRequest( 'https://lk.wildberries.ru/basket',
                                self.parse_item,
                                endpoint='execute',
                                session_id=1,
                                cache_args=['lua_source'],
                                args={'lua_source': delete_items,
                                'wait': 2,
                                },
                                )

        # $('.btn-withDotted-cross.j-basket-item-del')
