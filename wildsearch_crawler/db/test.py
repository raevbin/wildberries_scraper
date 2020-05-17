DB_ENGINE = "mysql+mysqldb://root:root@db:3306/test?charset=utf8"
MIGRATIONS_PATH = "migrations/test"


from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
engine = create_engine(DB_ENGINE)
Base = declarative_base()
Session = sessionmaker(bind=engine)
class TryModel(Base):
    __tablename__ = 'try'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    test = Column(String(250))

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"<try({self.id}, {self.name}>"


Base.metadata.create_all(engine)
