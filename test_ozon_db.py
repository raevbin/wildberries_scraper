from wildsearch_crawler.db.ozon import Session, CatalogModel as CT, ItemModel as IT
from wildsearch_crawler.db.ozon  import CostModel as CS
from wildsearch_crawler.db.ozon  import ReviewModel as RV, QuantityModel as QT
from wildsearch_crawler.db.ozon  import engine
from wildsearch_crawler.tools import ProxyLoader as PL, ProxyRotator as PR
from sqlalchemy.sql import text
session = Session()
conn = engine.connect()
s = session
models = '''
CatalogModel as CT, ItemModel as IT
CostModel as CS, ReviewModel as RV,
QuantityModel as QT, ProxyLoader as PL, ProxyRotator as PR
'''
