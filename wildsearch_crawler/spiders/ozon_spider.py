import logging
import scrapy
import json
import traceback
import re
from pprint import pprint
from wildsearch_crawler.tools import DeepDict, find_keys, find_value
from urllib.parse import quote
from .base_spider import BaseSpider
from wildsearch_crawler.settings import ERROR_TRACE_LEVEL
from wildsearch_crawler.db.ozon import CatalogModel, ItemModel, get_elements, Session, get_end_points_by_top_of_bush

logger = logging.getLogger('main')


class WildberriesSpider(BaseSpider):
    name = "oz"
    overwrite = False
    api_url = 'https://www.ozon.ru/api/composer-api.bx/page/json/v2?url='
    base_url = 'https://www.ozon.ru'

    custom_settings = {
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY':  1.0,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'ITEM_PIPELINES': {
            'wildsearch_crawler.ozon_pipelines.OzonGoodPipeline': 300,
        }
    }

    def convert_category_url_to_api(self, url):
        """Simple trick to get JSON with LOTS of data instead of HTML is to convert URL as follows:
        From /category/utyugi-10680/?layout_container=categoryMegapagination&layout_page_index=9&page=9
        To  https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=%2Fcategory%2Futyugi-10680%2F%3Flayout_container%3DcategoryMegapagination%26layout_page_index%3D8%26page%3D8
        """
        return f'{self.api_url}{quote(url)}'


    def convert_api_to_seo_url(self, url):
        return url.replace(self.api_url, self.base_url)

    def convert_seo_to_api_url(self, url):
        return url.replace(self.base_url, self.api_url)

    def add_pagination_params(self, url):
        """Trick to get first result page with pagination and 'nextPage' param"""
        return f'{url}?layout_container=categorySearchMegapagination&layout_page_index=1&page=1'

    def start_requests(self):
        try:
            item_id = getattr(self, 'item_id', None)
            self.limit = getattr(self, 'limit', None)
            item_objects = []

            if item_id:
                item_objects.extend(get_elements(item_id, ItemModel))

            item_cat_id = getattr(self, 'item_cat_id', None)
            if item_cat_id:
                item_objects.extend(get_elements(item_cat_id,
                                            ItemModel, CatalogModel.id,
                                            ItemModel.categories))

            item_art = getattr(self, 'item_art', None)
            if item_art:
                item_objects.extend(get_elements(item_art,
                                                        ItemModel, ItemModel.art))

            if item_objects:
                self.skip_variants = True
                for i, el in enumerate(item_objects):
                    if i == self.limit:
                        return
                    yield scrapy.Request(self.convert_seo_to_api_url(el.url),
                                            self.parse_good,
                                            cb_kwargs={'iter_variants': False,
                                                        'iter_options': False})
                return


            cat_id = getattr(self, 'cat_id', None) # <number>, <range>, all, endpoints

            if cat_id:
                objects = []
                if cat_id == 'endpoints':
                    objects = Session().query(CatalogModel
                                    ).filter_by(end_point=True).all()
                else:
                    # objects = get_elements(cat_id, CatalogModel)
                    objects = get_end_points_by_top_of_bush(cat_id)

                for i, el in enumerate(objects):
                    if i == self.limit:
                        return
                    yield scrapy.Request(self.convert_seo_to_api_url(el.url),
                    self.parse_category, cb_kwargs={'category_url': el.url})
                return

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise


    def get_good_data(self, data_text):
        data = json.loads(data_text)

        widget_data = data.get('widgetStates')

        def get_variants(widget_data):
            target_keys = find_keys('webAspects',widget_data)
            target_keys = find_value('aspects', widget_data, target_keys)

            def get_option(var_list):
                if var_list:
                    for var in var_list:
                        if var.get('active'):
                            d_var = DeepDict(var)
                            l_textRs = d_var.get('data.textRs')
                            if l_textRs:
                                return next(l_textRs).get('content')

            def split_variants(aspects):
                variants_ind = 0
                options_ind = 1
                for i, el in enumerate(aspects):
                    if el.get('type') in ['apparelPics']:
                        variants_ind = i
                        options_ind = 1 if i == 0 else 0
                return aspects[variants_ind], aspects[options_ind]

            for key in target_keys:
                out = {}
                data_str = widget_data.get(key)
                data = json.loads(data_str)
                aspects = data.get('aspects')
                # textBar, sizes
                # apparelPics
                if len(aspects) == 2:
                    variants, options = split_variants(aspects)
                    out['variants'] = variants.get('variants')
                    out['options'] = options.get('variants')
                    out['variant'] = get_option(out['variants'])
                    out['option'] = get_option(out['options'])
                else:
                    pass

                return out


        def get_characteristics(widget_data):
            target_keys = find_keys('characteristics',widget_data)
            target_keys = find_value('characteristics', widget_data, target_keys)
            out = {}
            for key in target_keys:
                list_ = []
                data_str = widget_data.get(key)
                data = json.loads(data_str)
                char_list = data.get('characteristics', [])
                if len(char_list) == 1:
                    list_.extend(char_list[0].get('short'))
                elif len(char_list) > 1:
                    list_.extend(char_list[1].get('short'))
                for el in list_:
                    key = el.pop('key')
                    out[key] = el
            return out

        def get_review(widget_data):
            target_keys = find_keys('reviewProductScore',widget_data)
            for key in target_keys:
                data_str = widget_data.get(key)
                return json.loads(data_str)

        def get_main_info(widget_data):
            target_keys = find_keys('webProductMainWidget', widget_data)
            for key in target_keys:
                data_str = widget_data.get(key)
                data = json.loads(data_str)
                return data.get('cellTrackingInfo',{}).get('product')

        def get_images(widget_data):
            target_keys = find_keys('webGallery', widget_data)
            for key in target_keys:
                data_str = widget_data.get(key)
                return json.loads(data_str).get('images')


        return {
            'main': get_main_info(widget_data),
            'images': get_images(widget_data),
            'review': get_review(widget_data),
            'characteristics': get_characteristics(widget_data),
            'variants': get_variants(widget_data),
            'overwrite': self.overwrite
        }


    def parse_good(self, serponse, parent_item=None,
                    iter_options=True, iter_variants=True, category_url=None):
        try:
            data = self.get_good_data(serponse.text)
            data['category_url'] = category_url
            variants = data.get('variants')

            if not parent_item:
                if data:
                    parent_item = data.get('main',{}).get('id')
            else:
                data['parent_item'] = parent_item

            if variants:

                if iter_variants and variants.get('variants'):
                    for el in variants.get('variants'):
                        if not el.get('active'):
                            # logger.debug(f'>>>>> try variant {el.get("link")}')
                            url = self.convert_category_url_to_api(el.get('link'))
                            yield scrapy.Request(url, self.parse_good,
                                                cb_kwargs={'iter_variants': False,
                                                            'parent_item': parent_item})

                if iter_options and variants.get('options'):
                    for el in variants.get('options'):
                        if not el.get('active'):
                            # logger.debug(f'>>>>> try option {el.get("link")}')
                            url = self.convert_category_url_to_api(el.get('link'))
                            yield scrapy.Request(url, self.parse_good,
                                                cb_kwargs={'iter_variants': False,
                                                            'iter_options': False,
                                                            'parent_item': parent_item})

            yield data

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))


    def parse_category(self, response, category_url):
        try:
            def find_goods_items(data):
                """We search for following patterns in JSON keys:

                searchResultsV2-226897-default-1
                searchResultsV2-193750-categorySearchMegapagination-2
                """
                for idx, val in data['widgetStates'].items():
                    if 'searchResultsV2' in idx:
                        return val

            def get_next_page(data):
                url = data.get('pageInfo', {}).get('url')
                if url:
                    url = url.split('?')[0]
                    shared_str = data.get('shared')
                    shared = json.loads(shared_str)
                    current_page = shared.get('catalog',{}).get('currentPage',0)
                    total_page = shared.get('catalog',{}).get('totalPages',0)
                    # current_page = current_page if current_page > 0 else 1
                    nex_page = current_page + 1
                    if nex_page <= total_page:
                        return  f'{url}?page={nex_page}'

            category_position = int(response.meta['current_position']) if 'current_position' in response.meta else 1

            category_data = json.loads(response.text)

            items_raw = find_goods_items(category_data)
            items = json.loads(items_raw)
            items_count = len(items['items'])

            current_position = category_position

            for i, item in enumerate(items['items']):
                # logger.debug(f'>>>>> {i} {item["link"]}')
                url = self.convert_category_url_to_api(item['link'])
                yield scrapy.Request(url, self.parse_good, cb_kwargs={'category_url':category_url})

                current_position += 1

            # follow pagination
            next_url = get_next_page(category_data)
            print('\n\n\n','next_url', next_url, '\n\n\n')
            # if 'nextPage' in [*category_data]:
            #     next_url = self.convert_category_url_to_api(category_data['nextPage'])
            if next_url:

                next_url = self.convert_category_url_to_api(next_url)
                logger.debug(f'>>> try nextPage {next_url}')
                yield scrapy.Request(
                    next_url,
                    self.parse_category, cb_kwargs={'category_url': category_url},
                    meta={
                        # 'category_url': category_url,
                        'category_position': category_position + items_count
                    }
                )
        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise
