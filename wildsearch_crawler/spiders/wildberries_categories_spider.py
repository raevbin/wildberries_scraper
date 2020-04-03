from datetime import datetime
import logging
import scrapy
import traceback
from .base_spider import BaseSpider
from urllib.parse import urlparse, urljoin
from wildsearch_crawler.db import Session, CatalogModel

logger = logging.getLogger('main')


class WildberriesCategoriesSpider(BaseSpider):

    name = "catalog"

    def start_requests(self):

        self.db = Session()
        try:
            self.base_preparation()

            yield scrapy.Request('https://www.wildberries.ru/services/karta-sayta',
                    self.parse,
                    errback=self.errback_httpbin,
                    dont_filter=True)
        except Exception as e:
            logger.error(traceback.format_exc(10))
            raise


    def base_preparation(self):
        self.db.query(CatalogModel).update({'recheck_found': False})
        self.db.commit()


    def appropriation_parent_id(self):
        logger.info('start appropriation_parent_id')

        def get_parent_id(url):
            list_url = url.split('/')
            if len(list_url)<=5:
                return 0
            parent_url = '/'.join(list_url[:-1])
            obl_parent = self.db.query(CatalogModel
                                        ).filter_by(url=parent_url).first()
            if obl_parent:
                return obl_parent.id

        without_upper_id = self.db.query(CatalogModel).\
                                            filter_by(upper_id=None).\
                                            order_by(CatalogModel.url).all()
        logger.info(f'count without_upper_id {len(without_upper_id)}')
        print('Data storage in progress, please wait.....')

        for el in without_upper_id:
            if el.url:
                el.upper_id = get_parent_id(el.url)
        print('\n')
        self.db.commit()

        count = len(self.db.query(CatalogModel).filter_by(upper_id=None).all())
        logger.info(f'repar count without_upper_id {count}')

    def spider_closed(self, spider, reason):
        try:
            self.db.commit()
            self.appropriation_parent_id()
            self.print_report()
        except Exception as e:
            logger.error(traceback.format_exc(10))
            raise



    def write(self, item):
        object = self.db.query(CatalogModel
                        ).filter_by(url=item.get('wb_category_url')).first()



        if not object:
            object = CatalogModel()
            object.name = item.get('wb_category_name')
            object.date_add = datetime.now()
            object.marketplace = 1
            object.url = item.get('wb_category_url')
            self.db.add(object)
        else:
            if item.get('wb_category_name') != object.name:
                object.recheck_newname = item.get('wb_category_name')
            object.recheck_found = True

        object.recheck_date = datetime.now()

        print(f'add {object.url}')


    def parse(self, response):
        start_url_parsed = urlparse(response.request.url)

        for url in response.css('#sitemap a'):
            url_parsed = urlparse(url.attrib['href'])
            full_url = urljoin(start_url_parsed.scheme + '://' + start_url_parsed.netloc, url_parsed.path)

            data = {
                'parse_date': datetime.now().isoformat(" "),
                'marketplace': 'wildberries',
                'wb_category_name': url.css('::text').get(),
                'wb_category_url': full_url
            }
            try:
                self.write(data)
            except Exception as e:
                logger.error(traceback.format_exc(10))
                raise

        return
