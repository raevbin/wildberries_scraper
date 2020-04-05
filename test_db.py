from wildsearch_crawler.db import Session, CatalogModel as CT, ItemModel as IT
from wildsearch_crawler.db import CostModel as CS, StockModel as ST
from wildsearch_crawler.db import ReviewModel as RV, OptionModel as OP, QuantityModel as QT
from wildsearch_crawler.tools import ProxyLoader as PL, ProxyRotator as PR
from wildsearch_crawler.db import engine, get_catalog_endpoints, get_elements_by_id
from sqlalchemy.sql import text
session = Session()
conn = engine.connect()
s = session
models = '''
 CatalogModel as CT, ItemModel as IT
 CostModel as CS, StockModel as ST
 ReviewModel as RV, OptionModel as OP, QuantityModel as QT
 ProxyLoader as PL, ProxyRotator as PR
'''
def get_endpoints():
    for el in get_catalog_endpoints():
        yield el.id, el.url

endpoint = get_endpoints()
