# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import traceback
from pprint import pprint
from .db import Session, CatalogModel, ItemModel
from .db import CostModel, StockModel, ReviewModel, OptionModel, QuantityModel
from wildsearch_crawler.tools import DeepDict

logger = logging.getLogger('main')


def log(*args):
    stack = ''
    for el in args:
        stack = f'{stack} {el}'
    logger.debug(stack)


class WildsearchCrawlerPipeline(object):
    def __init__(self):
        self.db = Session()

    def process_item(self, item, spider):
        func = getattr(self, f'proc_{spider.name}')
        try:
            func(item)
        except Exception as e:
            logger.error(traceback.format_exc(10))
            raise

        return item

    def proc_wb_cost(self, item):

        current_date = datetime.now()

        def proc_option(item_id, option_data):

            option_param = {
                'item_id': item_id,
                'wb_option_id': option_data.get('optionId')
            }
            option_mod = self.db.query(OptionModel).\
                        filter_by(**option_param).first()

            if not option_mod:
                option_param['date_add'] = current_date
                option_param['name'] = option_data.get('name')
                option_mod = OptionModel(**option_param)
                self.db.add(option_mod)
                self.db.commit()

            quantities = option_data.get('stocks')

            for quantity_data in quantities:
                quantity_mod = QuantityModel(**{
                    'id_date': current_date,
                    'option_id': option_mod.id,
                    'warehouse_id': quantity_data.get('wh'),
                    'quantity': quantity_data.get('qty'),
                })
                self.db.add(quantity_mod)

            self.db.commit()


        def proc_product(id, product_data):

            item_mod = self.db.query(ItemModel).filter_by(id=id).first()
            if not item_mod:
                raise Exception('item not found')
            item_mod.recheck_date = current_date

            cost_mod = CostModel(**{
                'item_id': item_mod.id,
                'id_date': current_date,
                'cost': product_data.get('price'),
                'cost_new': product_data.get('salePrice'),
                'cost_discount': product_data.get('extended.basicPrice'),
                'cost_discount2': product_data.get('extended.promoPrice'),
                # 'cost_discount3': product_data.get('extended.promoPrice'),
            })
            self.db.add(cost_mod)

            options = product_data.get('sizes')

            for option_data in options:
                proc_option(item_mod.id, option_data)

            logger.info(f'Pipeline item {cost_mod}')

        data = DeepDict(item, log=log, log_args=[f'proc_wb_cost {item} \
                                                                data error'])
        art_id_dict = data.get('art_id_dict')
        products = data.get('data.products')
        for product_data in products:
            id = art_id_dict.get(str(product_data.get('id')))
            proc_product(id, product_data)

        self.db.commit()
        return item



    def proc_wb(self, item):
        current_date = datetime.now()

        products = self.db.query(ItemModel).filter_by(url=item.get('product_url')).all()
        product = None
        if products:
            product = products[0]
        else:
            product = ItemModel()

        if product.id:
            product.recheck_date = current_date

        else:
            product.category_id = item.get('category_id')
            product.name =  item.get('product_name')
            product.art =  item.get('wb_id')
            product.parent_art =  item.get('wb_parent_id')
            product.marketplace = 1
            product.url =  item.get('product_url')
            product.img_urls =  item.get('image_urls')
            product.date_add = current_date
        self.db.add(product)

        self.db.commit()
        stock = StockModel(**{
            'bought': item.get('wb_purchases_count'),
            'instock': item.get('instock'),
            'id_date': current_date,
            'item_id': product.id
        })

        review = ReviewModel(**{
            'item_id': product.id,
            'id_date': current_date,
            'reviews': item.get('wb_reviews_count'),
            'reviews_rate': item.get('wb_rating')
        })
        self.db.add(stock)
        self.db.add(review)
        self.db.commit()

        logger.info(f'Pipeline item {product} {stock} {review}')

        return item

    def proc_catalog(self, item):
    #'''function moved to spider'''

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

        self.db.commit()
