# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import traceback
from pprint import pprint
from .db.ozon import Session, CatalogModel, ItemModel
from .db.ozon import CostModel, ReviewModel, QuantityModel
from wildsearch_crawler.tools import DeepDict
from wildsearch_crawler.settings import ERROR_TRACE_LEVEL

logger = logging.getLogger('main')


class OzonCatalogPipeline(object):
    base_addr = 'https://www.ozon.ru'

    def __init__(self):
        self.db = Session()

    def process_item(self, item, spider):
        try:
            self.save(item)
        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise

    def save(self, item):
        url = f"{self.base_addr}{item.get('url')}"

        object = self.db.query(CatalogModel
                        ).filter_by(url=url).first()

        if not object:
            object = CatalogModel()
            object.name = item.get('title')
            object.date_add = datetime.now()
            object.marketplace = 2
            object.url = url
            object.ozon_id = item.get('id')
            object.upper_ozon_id = item.get('upper_ozon_id') if item.get('upper_ozon_id') else 0

            self.db.add(object)
        else:
            if item.get('title') != object.name:
                object.recheck_newname = item.get('title')
            object.recheck_found = True

        object.end_point = item.get('end_point')
        object.recheck_date = datetime.now()

        self.db.commit()
        logger.info(f'Saved category {object.id} {object.url} end_point:{object.end_point}')


class OzonGoodPipeline(object):
    def __init__(self):
        self.db = Session()

    def process_item(self, item, spider):
        try:
            current_date = datetime.now()
            overwrite = item.get('overwrite')
            item = DeepDict(item)
            product = self.db.query(ItemModel).filter_by(art=item.get("main.id")).first()
            if not product:
                product = ItemModel()
                overwrite = True

            if product.id:
                product.recheck_date = current_date

            else:
                product.art =  item.get("main.id")
                product.parent_art =  item.get('parent_item')
                product.marketplace = 2
                product.date_add = current_date

            if overwrite:
                url = item.get('main.link').split('?')[0]
                product.url = url
                product.name = item.get('main.title')
                product.specification = item.get('characteristics')._dict
                product.img_urls =  list(item.get('images'))
                product.seller_id = item.get('main.sellerId')
                product.brand_id = item.get('main.brandId')
                product.storehouse_id = item.get('main.storehouseId')


            category = self.db.query(CatalogModel).filter_by(url=item.get('category_url')).first()
            if category:
                product.categories.append(category)

            self.db.add(product)
            self.db.commit()

            review = ReviewModel(**{
                'item_id': product.id,
                'id_date': current_date,
                'reviews': item.get('review.reviewsCount'),
                'reviews_rate': item.get('review.totalScore')
            })
            self.db.add(review)


            cost = CostModel(**{
                'item_id': product.id,
                'id_date': current_date,
                'cost' : item.get('main.price'),
                'cost_new':item.get('main.finalPrice'),
            })
            self.db.add(cost)
            self.db.commit()

            logger.info(f'Saved item {product.id} {product.url}')

            return item
        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise




class OzonQuantityPipeline(object):
    def __init__(self):
        self.db = Session()

    def process_item(self, item):
        current_date = datetime.now()
        for data in item.get('list'):
            quantity = QuantityModel(**{
                'item_id': data.get('item_id'),
                'id_date': current_date,
                'quantity': data.get('quantity'),
            })
            self.db.add(quantity)
            logger.info(f'Saved item_id:{quantity.item_id}, art:{data.get("art")} qty:{quantity.quantity}')

        self.db.commit()
