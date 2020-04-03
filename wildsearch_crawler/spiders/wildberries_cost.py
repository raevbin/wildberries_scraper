import datetime
import logging
import math
import scrapy
import json
from pprint import pprint


from .base_spider import BaseSpider
from urllib.parse import urlparse, urljoin, urlencode
from wildsearch_crawler.db import Session, CatalogModel, ItemModel, get_elements_by_id


logger = logging.getLogger('main')


class WildberriesCategoriesSpider(BaseSpider):

    name = "wb_cost"
    base_url = 'https://nm-2-card.wildberries.ru/enrichment/v1/api?'
    base_param = [
        ('spp', 0),
        # ('couponsGeo', '3,12,15,18'),
        ('pricemarginCoeff', 1.0),
        ('reg', 0),
        ('appType', 1)
    ]
    portion = 1

    def start_requests(self):
        item_ids = getattr(self, 'item_ids', None)

        id_art_list = []
        if item_ids:
            objects = get_elements_by_id(item_ids, ItemModel)
            id_art_list.extend([{str(el.art): el.id} for el in objects])

        catalog_ids = getattr(self, 'catalog_ids', None)

        if catalog_ids:
            objects = get_elements_by_id(catalog_ids,
                                        ItemModel, ItemModel.category_id)
            id_art_list.extend([{str(el.art): el.id} for el in objects])

        for art_id_dict in self.get_portion(id_art_list):

            art_str = ','.join(list(art_id_dict.keys()))
            base_param = urlencode(self.base_param, doseq=True)
            url = f'{self.base_url}{base_param}&nm={art_str}'

            yield scrapy.Request(url, self.parse,
                                        cb_kwargs={'art_id_dict': art_id_dict})



    def get_portion(self, param_list):
        l = len(param_list)
        if l > self.portion:
            r = math.ceil(l / self.portion)
        else:
            r = 1

        for i in range(r):
            start = i*self.portion
            end = start + self.portion
            out = {}
            for el_dict in param_list[start:end]:
                out.update(el_dict)
            yield out


    def parse(self, response, art_id_dict):
        logger.info(f'parse {art_id_dict} {response.url} ')
        # print('art_id_dict', art_id_dict)
        data = json.loads(response.text)
        data['art_id_dict'] = art_id_dict
        yield data

    
