import scrapy
from bs4 import BeautifulSoup
import logging
import time
import math
import json
import re
from pprint import pprint
import traceback
from selenium import webdriver
from .base_spider import BaseSpider
from wildsearch_crawler.db.ozon import CatalogModel, ItemModel, get_elements
from wildsearch_crawler.tools import ChromeDriverBoot
from wildsearch_crawler.settings import ERROR_TRACE_LEVEL, SELENOID_STATUS_URL
from wildsearch_crawler.ozon_pipelines import OzonQuantityPipeline

logger = logging.getLogger('main')


class OzonQuantitySpider(BaseSpider):
    name = 'oz_qty'
    portion = 10
    count_portion = 2
    use_proxy = True
    errors = []

    def start_requests(self):
        try:
            self.db = OzonQuantityPipeline()
            art_id_list = []
            objects = []

            item_id = getattr(self, 'item_id', None)
            if item_id:
                objects = get_elements(item_id, ItemModel)

            item_cat_id = getattr(self, 'item_cat_id', None)
            if item_cat_id:
                objects = get_elements(item_cat_id,
                                            ItemModel, CatalogModel.id,
                                            ItemModel.categories)
            item_art = getattr(self, 'item_art', None)
            if item_art:
                objects = get_elements(item_art, ItemModel, ItemModel.art)
            art_id_list.extend([{el.art: el.id} for el in objects])

            yield scrapy.Request(SELENOID_STATUS_URL,
                    self.manage,
                    dont_filter=True, cb_kwargs={'art_id_list': art_id_list},
                    meta={'off_proxy': True}
                    )

        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
            raise

    def manage(self, response, art_id_list):

        status_data = json.loads(response.text)
        session_quota = status_data.get('total') - status_data.get('used')
        len_list = len(art_id_list)
        quota = session_quota
        minimum_lot = self.portion * self.count_portion
        declared_quota = math.ceil(len_list/minimum_lot) if minimum_lot else 1

        if not self.use_proxy:
            if declared_quota < session_quota:
                quota = declared_quota
            lot_len =  math.ceil(len_list/quota)
        else:
            if declared_quota > session_quota:
                quota = declared_quota
            lot_len = self.count_portion * self.portion
            if lot_len == 0:
                lot_len = len_list

        for num_part in range(quota):
            start = lot_len * num_part
            end = start + lot_len
            out = art_id_list[start:end]
            if len(out):
                yield scrapy.Request(SELENOID_STATUS_URL,
                        self.parse,
                        dont_filter=True, cb_kwargs={'art_id_list': out},
                        meta={'off_proxy': True})


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

    def parse(self, response, art_id_list):
        logger.info(f'Parse {art_id_list}')
        try:
            parser = OzonSeleniumParser(use_proxy=self.use_proxy)
        except Exception as e:
            logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))

        for art_id_dict in self.get_portion(art_id_list):
            try:
                self.db.process_item({'list': parser.get_quantity(art_id_dict)})
            except Exception as e:
                logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
                mess = f'\nError. This task was not fully processed: {art_id_dict}'
                logger.error(mess)
                self.errors.append(mess)
        return None




class OzonSeleniumParser(object):
    js_templ = '''
    ;(function() {
          var request = ()=>{
            var url = "URL";
            var data = DATA;
            var mxhr = new XMLHttpRequest();
            var strParam = JSON.stringify(data);
            mxhr.open('POST', url , false);
            mxhr.setRequestHeader('Content-Type', 'application/json');
            mxhr.send(strParam);
            var input = null;
            try {
                input = JSON.parse(mxhr.responseText);
              }
            catch (err) {
              input = mxhr.responseText;
              console.error(err, input);

            }
            finally {
              mxhr.abort();
            }
            return input
          }
          request();
    }());
    '''

    def __init__(self, use_proxy=True, use_agent=False):
        self.driver = ChromeDriverBoot().get('https://www.ozon.ru/',
                                    use_proxy=use_proxy,
                                    use_agent=use_agent)

    def get_quantity(self, art_id_dict):
        self.art_id_dict = art_id_dict
        add_url = 'https://www.ozon.ru/webapi/composer-api.bx/_action/addToCart'
        js = self.js_templ.replace('URL', add_url)
        js = js.replace('DATA', self.get_param_add_baket())
        self.driver.execute_script(js)

        self.driver.get('https://www.ozon.ru/cart')
        count_quantity = len(re.findall(r'maxQuantity', self.driver.page_source))
        if not count_quantity:
            if len(re.findall(r'Корзина пуста', self.driver.page_source)):
                logger.error(f'ERROR, No items have been added to the cart. {self.art_id_dict}')
                raise Exception(f'ERROR, No items have been added to the cart. {self.art_id_dict}')

            else:
                for _ in range(3):
                    time.sleep(3)
                    self.driver.refresh()
                    count_quantity = len(re.findall(r'maxQuantity', self.driver.page_source))
                    print('count_quantity',count_quantity)
                    if count_quantity:
                        break

        out_data_list = []
        if count_quantity:
            data_list = self.get_data()
            out_data_list = self.proc_data(data_list)

        for el in self.art_id_dict:
            out_data_list.append({
                'item_id': self.art_id_dict[el],
                'art': el,
                'quantity': 0,
                'count_elem_maxQuantity': count_quantity
            })

        del_url = 'https://www.ozon.ru/webapi/composer-api.bx/page/json/v2?url=%2Fcart%3Fdelete%3Dselectedtab0'
        js = self.js_templ.replace('URL', del_url)
        js = js.replace('DATA', '{}')
        self.driver.execute_script(js)

        return out_data_list

    def __del__(self):
        try:
            self.driver.close()
        except Exception as e:
            pass


    def proc_data(self,data_list):
        out_data_list = []
        for data in data_list:
            id = self.art_id_dict.pop(int(data.get('id')))

            out_data_list.append({
                'item_id': id,
                'art': int(data.get('id')),
                'quantity': data.get('maxQuantity')
            })

        return out_data_list


    def get_data(self):
        bs = BeautifulSoup(self.driver.page_source, 'html.parser')
        scripts = bs.select('script[id ^="state-split"]')
        data_list = []
        for scr_el in scripts:
            data = json.loads(scr_el.contents[0])
            data = data.get('items')
            data_list.extend(data)
        return data_list


    def get_param_add_baket(self):
        param_list = []
        for art in self.art_id_dict:
            param_list.append({'id':art, 'quantity':1})
        return json.dumps(param_list)
