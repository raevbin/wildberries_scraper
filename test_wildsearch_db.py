from wildsearch_crawler.db.wildsearch import Session, CatalogModel as CT, ItemModel as IT
from wildsearch_crawler.db.wildsearch  import CostModel as CS
from wildsearch_crawler.db.wildsearch  import ReviewModel as RV, QuantityModel as QT
from wildsearch_crawler.db.wildsearch  import engine, get_catalog_endpoints
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
def get_endpoints():
    for el in get_catalog_endpoints():
        yield el.id, el.url

endpoint = get_endpoints()



it = IT()
it.name = 'test'
# cat = CT()
# cat.name = 'test _cat'
# it.categories.append(cat)
s.add(it)
s.commit()
# s.add(cat)
# s.commit()
n = s.query(CT).filter_by(id=10).first()
# n.items.append(it)
it.categories.append(n)
s.commit()
