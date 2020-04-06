from .settings import DB_ENGINE
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import FLOAT, DateTime, SmallInteger, BOOLEAN, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text as SqlText
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
    upper_id = Column(Integer)
    url = Column(String(250))
    date_add = Column(DateTime)
    newid = Column(Integer)
    marketplace = Column(SmallInteger)
    recheck_date = Column(DateTime)
    recheck_newname = Column(String(250))
    recheck_found = Column(BOOLEAN)
    items = relationship("ItemModel",
                    secondary=cat_item_table)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Catalog({self.id}, {self.name}>"


class ItemModel(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('catalog.id'))
    name = Column(String(250))
    art = Column(Integer)
    parent_art = Column(Integer)
    marketplace = Column(SmallInteger)
    seller = Column(String(100))
    url = Column(String(250))
    img_urls = Column(JSON)
    date_add = Column(DateTime)
    newid = Column(Integer)
    recheck_date = Column(DateTime)
    recheck_found = Column(BOOLEAN)
    specification = Column(JSON)
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

class StockModel(Base):
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    id_date = Column(DateTime)
    bought = Column(Integer)
    instock = Column(Integer)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Stock({self.id}, item:{self.item_id}, instock:{self.instock}>"


class ReviewModel(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    id_date = Column(DateTime)
    reviews = Column(Integer)
    reviews_rate = Column(Integer)

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Review({self.id}, item:{self.item_id}, rate:{self.reviews_rate}>"



class OptionModel(Base):
    __tablename__ = 'opt'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'))
    date_add = Column(DateTime)
    wb_option_id = Column(Integer)
    recheck_date = Column(DateTime)
    name = Column(String(30))

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Optiion({self.id}, item:{self.item_id}, {self.name}>"





class QuantityModel(Base):
    __tablename__ = 'quantity'

    id = Column(Integer, primary_key=True)
    option_id = Column(Integer, ForeignKey('opt.id'))
    id_date = Column(DateTime)
    warehouse_id = Column(Integer)
    quantity = Column(Integer)


    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Quantity({self.id}, opt:{self.option_id}, wh:{self.warehouse_id}, qty:{self.quantity}>"




class ProxyModel(Base):
    __tablename__ = 'proxy'
    id = Column(Integer, primary_key=True)
    ip = Column(String(50))
    port = Column(Integer)
    protocol = Column(String(10))
    authorization = Column(String(50)) # login:passoword
    source = Column(String(50)) # file, scylla, ...
    group = Column(String(10)), # characterization groups, for example: stable, paid, publicly
    latency = Column(Integer) # ms
    is_anonymous = Column(BOOLEAN)
    country = Column(String(10)) # US, UA , RF ....
    created_at = Column(DateTime)
    stats = relationship("StatProxyModel", back_populates="proxy")
    use_postponed_to = Column(DateTime)


    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<Proxy({self.__str__()})>"

    def __str__(self):
        authoriz = ''
        if self.authorization:
            authoriz = f'{self.authorization}@'
        return f"{self.protocol}://{authoriz}{self.ip}:{self.port}"


class StatProxyModel(Base):
    __tablename__ = 'stat'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('proxy.id'))
    proxy = relationship("ProxyModel", back_populates="stats")
    date = Column(DateTime)
    is_well = Column(BOOLEAN)
    status = Column(Integer) # response status : 200, 400, 111
    description = Column(String(250))

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<StatProxy({self.date}, {self.status}>"




Base.metadata.create_all(engine)

# s.query(IT).join(IT.categories, aliased=True).filter_by(id=11).all()


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


def get_catalog_endpoints():
    class Element:
        def __init__(self, id, url):
            self.id = id
            self.url = url

    conn = engine.connect()
    sql = SqlText('''SELECT id, url FROM catalog
            WHERE id not in (SELECT upper_id FROM catalog
                            GROUP BY upper_id HAVING upper_id is not NULL)''')
    res = conn.execute(sql).fetchall()
    out = [Element(el[0],el[1]) for el in res]
    return out
