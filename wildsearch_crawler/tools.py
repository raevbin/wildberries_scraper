import redis
import requests
from urllib.parse import urlencode
from datetime import datetime, date, timedelta
import csv
import re
from .db import Session, ProxyModel, StatProxyModel
from wildsearch_crawler.settings import SCYLLA_URL, PROXY_POSTPONE_ON
import logging
logger = logging.getLogger('main')


def date_for_json(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()


class DeepDict(dict):

    def __init__(self, dict_obj, log=print, log_args=()):
        self._dict = dict_obj if dict_obj else {}
        self._log = log
        self._log_args = log_args

    def log(self, message):
        mess = list(self._log_args) + [message]
        self._log(*mess)

    def _list(self, array, default):
        for el in array:
            yield self._out(el, default)

    def _out(self, for_out, default):
        if type(for_out).__name__ == 'dict':
            return DeepDict(for_out,  self._log, self._log_args)

        if type(for_out).__name__ == 'list':
            return self._list(for_out, default)

        return for_out if for_out is not None else default

    def __iter__(self):
        for el in self._dict:
            yield self._out(el, None)

    def __repr__(self):
        return repr(self._dict)

    def __len__(self):
        return len(self._dict)

    def keys(self):
        return self._dict.keys()

    def get(self, selector, default=None):
        key_list = selector.split('.')

        def get_value(_key_list, el):
            val = el.get(_key_list[0])
            if type(val).__name__ == 'dict' and len(_key_list) > 1:
                return get_value(_key_list[1:], val)
            return val
        result = get_value(key_list, self._dict)

        if result is None:
            self.log('{0} element no fond'.format(selector))

        return self._out(result, default)





class ProxyLoader(object):

    def __init__(self):
        self.db = Session()
        self.scylla_url = SCYLLA_URL

    def from_scylla(self):
        def request(page=0, total_page=0):
            if page > total_page:
                return None

            params = {
                'https': True,
                'lomit': 130
            }
            if page:
                params['page'] = page
            response = requests.get(
                        f"{self.scylla_url}?{urlencode(params, doseq=True)}")
            if response.status_code == 200:
                data = response.json()
                if len(data.get('proxies')) != 0:
                    return data


        res = request()
        while res:
            data_list = res.get('proxies')
            total_page = res.get('total_page')
            page = res.get('page')
            for data in data_list:
                self._load(**{
                    "ip": data.get('ip'),
                    "port": data.get('port'),
                    "created_at": datetime.now(),
                    "latency": data.get('latency'),
                    "is_anonymous": data.get('is_anonymous'),
                    'protocol': 'https' if data.get('is_https') else 'http',
                    "country": data.get('country'),
                    'source': 'scylla',
                    'group': 'publicly',
                })
            page = page + 1
            res = request(page, total_page)

    def from_csv(self, file_name, group=None):
        with open(file_name, newline='') as csvfile:
          spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
          for i, row in enumerate(spamreader):
              if i > 0:
                  self._load(**{
                      "ip": row[1],
                      "port": row[2],
                      'authorization': f'{row[3]}:{row[4]}',
                      "created_at": datetime.now(),
                      'protocol': row[0],
                      'source': file_name,
                      'group': group,
                  })





    def _load(self,**kwargs):
        elements = ["ip", "port", "protocol"]
        filter = {}
        mess = 'add proxy to BD'
        for el in elements:
            filter[el] = kwargs.get(el)

        proxy = self.db.query(ProxyModel).filter_by(**filter).first()


        if not proxy:
            proxy = ProxyModel(**kwargs)
            proxy.use_postponed_to = datetime.now()

        else:
            if kwargs.get('authorization'):
                proxy.authorization = kwargs.get('authorization')
            if kwargs.get('group'):
                proxy.group = kwargs.get('group')
            if kwargs.get('latency'):
                proxy.latency = kwargs.get('latency')
            mess = 'updated proxy in BD'

        self.db.add(proxy)
        logger.info(f'{mess} from {kwargs.get("source")}: {proxy}')

        self.db.commit()








class ProxyRotator(object):
    redis_def_config = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }
    def __init__(self,
                redis_config=None,
                redis_prefix='proxy_rotator',
                reload=False,
                **filtres,
                # protocol='https',
                # country=None,
                # use_postponed_to=None
                ):
        config = redis_config if redis_config else self.redis_def_config
        self.rdb = redis.Redis(**config)
        self.db = Session()
        self.prefix = redis_prefix
        self.filtres = filtres

        has_set = self.rdb.get(f'{self.prefix}_has_set')
        if (not has_set) or reload:
            # print('if (not has_set) or reload:', has_set, reload)
            self._load()

    def _load(self):
        if self.filtres.get('protocol')=='all':
            self.filtres.pop('protocol')
        proxy_list = self.db.query(ProxyModel).\
                filter_by(**self.filtres).\
                filter(ProxyModel.use_postponed_to < datetime.now()).\
                all()

        proxy_list = [str(el) for el in proxy_list]
        curr_list = self.get_proxy_list()

        curr = set(curr_list)
        inp = set(proxy_list)
        diff = list(inp - curr)
        if diff:
            self.rdb.lpush(f'{self.prefix}_proxy_list', *diff)
            self.rdb.set(f'{self.prefix}_has_set', 1)

    def reload(self, **filtres):
        self.filtres = filtres
        self._load()

    def reset(self):
        self.rdb.delete(f'{self.prefix}_proxy_list')
        self.rdb.delete(f'{self.prefix}_has_set')


    def delete(self, element, message=''):
        self.rdb.lrem(f'{self.prefix}_proxy_list',1 , element)
        param = {
            'ip': re.findall(r'\d+.\d+.\d+.\d+', element)[0],
            'protocol': re.findall(r'^\w+', element)[0],
            'port':  int(re.findall(r'\d+$', element)[0]),
        }
        proxy = self.db.query(ProxyModel).filter_by(**param).first()
        if proxy:
            stat = StatProxyModel(**{
                'date': datetime.now(),
                'is_well': False,
                'description': message
            })
            proxy.stats.append(stat)
            proxy.use_postponed_to = datetime.now() + timedelta(minutes=PROXY_POSTPONE_ON)
            self.db.commit()


    def get_proxy_list(self):
        out = []
        for el in self.rdb.lrange(f'{self.prefix}_proxy_list', -1000, 1000):
            out.append(el.decode())
        return out

    def __iter__(self):
        for addr in self.get_proxy_list():
            yield addr.decode()


    def next(self):
        addr = self.rdb.rpop(f'{self.prefix}_proxy_list')
        if addr:
            addr = addr.decode()
        else:
            return None
        self.rdb.lpush(f'{self.prefix}_proxy_list', addr)
        return addr
