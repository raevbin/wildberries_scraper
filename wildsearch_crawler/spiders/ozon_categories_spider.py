import datetime
import logging
import re
import json
import scrapy
from wildsearch_crawler.tools import DeepDict, find_keys
from .base_spider import BaseSpider
from wildsearch_crawler.settings import ERROR_TRACE_LEVEL
from wildsearch_crawler.db.ozon import CatalogModel, Session

logger = logging.getLogger('main')


class WildberriesBrandsSpider(BaseSpider):
    name = "oz_catalog"
    start_urls = ['https://www.ozon.ru/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'wildsearch_crawler.ozon_pipelines.OzonCatalogPipeline': 300,
        }
    }
    base_addr = 'https://www.ozon.ru'

    def get_catalog_root_element(self, response):
        name_list = [
            '/category/elektronika',
            '/category/dom-i-sad',
            '/category/odezhda-obuv-i-aksessuary',
            '/category/detskie-tovary',
            '/category/krasota-i-zdorove',
            '/category/produkty-pitaniya',
            '/category/supermarket'
        ]
        for name in name_list:
            elems = response.xpath(f'//a[starts-with(@href,"{name}")]/..')
            if elems:
                return elems[0]

    def spider_opened(self, spider):
        logger.info(f'Spider opened: {spider.name}')

        self.base_preparation()


    def base_preparation(self):
        logger.info('Base preparation....')
        db = Session()
        db.query(CatalogModel).update({'recheck_found': False})
        db.commit()

    def parse(self, response):
        logger.info('Start parse')
        try:
            catalog_el = self.get_catalog_root_element(response)
            for i, el_a in enumerate(catalog_el.css('a')):
                root_data = self.get_root_data(el_a)
                if root_data:
                    id = root_data.get('id')
                    if id:
                        api_url = 'https://www.ozon.ru/webapi/cms-api.bx/menu/category/child/v1?categoryId={0}'.format(id)
                        logger.info('parse url {0}'.format(api_url))
                        yield scrapy.Request(api_url, self.parse_cat_element,
                                cb_kwargs={'root_data': root_data})
        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))


    def parse_cat_element(self, response, root_data):
        try:

            in_data = json.loads(response.text)
            root_data['categories'] = in_data.get('categories')
            out_list = []
            revision_list = []

            def get_data(data, upper_ozon_id=None):
                categories = data.pop('categories', None)
                data.pop('cellTrackingInfo', None)
                data['upper_ozon_id'] = upper_ozon_id
                if categories:
                    data['end_point'] = False
                    out_list.append(data)
                    for el in categories:
                        get_data(el, data.get('id'))
                else:
                    revision_list.append(data)

            get_data(root_data)


            for el in revision_list:
                api_url = 'https://www.ozon.ru/api/composer-api.bx/page/json/v2?url={0}'.format(el.get("url"))
                logger.info('parse url {0}'.format(api_url))
                yield scrapy.Request(api_url, self.parse_end_point,
                        cb_kwargs={'data': el})

            for el in out_list:
                yield el

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))


    def parse_end_point(self, response, data):
        try:
            penult_id = int(data.get('id'))

            resp_data = json.loads(response.text)
            widget = resp_data.get('widgetStates')
            w_keys = find_keys('searchResultsFilters', widget)
            end_point_categories = []
            if w_keys:
                srf_str = widget.get(w_keys[0])
                srf_data = json.loads(srf_str)
                cat_data = srf_data.get('categories')
                cat_data = DeepDict(cat_data)
                root_param = srf_data.get('urlCategoryQueryParam')

                for el in cat_data:
                    if str(penult_id) == el.get('info.id'):
                        end_point_categories = el.get('categories')

                for cat in end_point_categories:

                    url = '/{0}/{1}/'.format(root_param, cat.get("info.urlValue"))
                    out_data = {
                                'id': cat.get('info.id'),
                                'url': url,
                                'title': cat.get('info.name'),
                                'upper_ozon_id': data.get('id'),
                                'end_point': True
                                }
                    yield out_data

                data['end_point'] = False if end_point_categories else True
                yield data

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))



    def get_root_data(self, a_element):
        href = a_element.attrib.get('href')
        if re.findall(r'category', href ):
            id_list = re.findall(r'-(\d+)', href)
            data = {
                'id': id_list[0] if id_list else None,
                'title': a_element.css('span::text').get(),
                'url': href
            }
            return data
