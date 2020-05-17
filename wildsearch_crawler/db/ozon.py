from wildsearch_crawler.settings import OZ_DB_ENGINE
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import FLOAT, DateTime, SmallInteger, BOOLEAN, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text as SqlText
DB_ENGINE = OZ_DB_ENGINE
engine = create_engine(DB_ENGINE)
Session = sessionmaker(bind=engine)

Base = declarative_base()


cat_item_table = Table('cat_item', Base.metadata,
    Column('category_id', Integer, ForeignKey('catalog.id')),
    Column('item_id', Integer, ForeignKey('item.id')))


class CatalogModel(Base):
    __tablename__ = 'catalog'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    ozon_id = Column(Integer)
    upper_ozon_id = Column(Integer)
    url = Column(String(250))
    date_add = Column(DateTime)
    newid = Column(Integer)
    marketplace = Column(SmallInteger)
    recheck_date = Column(DateTime)
    recheck_newname = Column(String(250))
    recheck_found = Column(BOOLEAN)
    end_point = Column(BOOLEAN)
    items = relationship("ItemModel",
                    secondary=cat_item_table)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Catalog({self.id}, {self.name}>"


class ItemModel(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    art = Column(Integer)
    parent_art = Column(Integer)
    marketplace = Column(SmallInteger)
    seller_id = Column(Integer)
    brand_id = Column(Integer)
    url = Column(String(250))
    img_urls = Column(JSON)
    date_add = Column(DateTime)
    newid = Column(Integer)
    recheck_date = Column(DateTime)
    recheck_found = Column(BOOLEAN)
    specification = Column(JSON)
    storehouse_id = Column(Integer)
    categories = relationship("CatalogModel",
                    secondary=cat_item_table)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Item({self.id}, {self.name}, {self.art}>"

class CostModel(Base):
    __tablename__ = 'cost'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    id_date = Column(DateTime)
    cost = Column(FLOAT)
    cost_new = Column(FLOAT)
    cost_discount = Column(FLOAT)
    cost_discount2 = Column(FLOAT)
    cost_discount3 = Column(FLOAT)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Cost({self.id}, item:{self.item_id}, {self.cost}>"


class ReviewModel(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    id_date = Column(DateTime)
    reviews = Column(Integer)
    reviews_rate = Column(FLOAT)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Review({self.id}, item:{self.item_id}, rate:{self.reviews_rate}>"



class QuantityModel(Base):
    __tablename__ = 'quantity'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    id_date = Column(DateTime)
    quantity = Column(Integer)


    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Quantity({self.id}, item:{self.item_id}, qty:{self.quantity}>"




Base.metadata.create_all(engine)



def get_elements(param, model, element=None, relation=None):
    element = model.id if not element else element
    ''' param: <str>
        1,2,3,4,5,6-20
        all
    '''
    session = Session()
    objects = []
    if param == 'all':
        objects = session.query(model).all()
    else:
        param_list = param.split(',')
        ids_list = []
        for param in param_list:
            param_range = param.split('-')
            if len(param_range) == 2:
                first = int(param_range[0])
                second = int(param_range[1])+1
                ids_list.extend(list(range(first,second)))
            else:
                ids_list.append(int(param_range[0]))

        if relation:
            objects = session.query(model).join(relation, aliased=True).\
                                            filter(element.in_(ids_list)).all()
        else:
            objects = session.query(model).filter(element.in_(ids_list)).all()

    if objects:
        return [ el for el in objects]
    else:
        return []
