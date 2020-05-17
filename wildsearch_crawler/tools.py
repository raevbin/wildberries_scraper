import redis
import requests
from urllib.parse import urlencode
from datetime import datetime, date, timedelta
import csv
import re
import os
import uuid
import time
from tempfile import gettempdir
from selenium import webdriver
import pathlib
import zipfile
import traceback
from fake_useragent import UserAgent

from .db.wildsearch import Session, ProxyModel, StatProxyModel
from wildsearch_crawler.settings import SCYLLA_URL, PROXY_POSTPONE_ON, SELENOID_HUB, UPLOAD_NEW_PROXIES_IF_LESS_THAN
import logging



logger = logging.getLogger('main')



def find_keys(word,data_dict):
    keys_str = ','.join(data_dict.keys())
    return re.findall(f'({word}.+?),',keys_str)


def find_value(word, data_dict, keys):
    for key in keys:
        val = data_dict.get(key)
        res = re.findall(word,val)
        if res:
            yield key


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
                use_postponed=False,
                **filtres,
                # protocol='https',
                # country=None,
                # use_postponed_to=None
                ):
        config = redis_config if redis_config else self.redis_def_config
        self.rdb = redis.Redis(**config)
        self.db = Session()
        self.prefix = redis_prefix
        self.use_postponed = use_postponed
        self.filtres = filtres


        has_set = self.rdb.get(f'{self.prefix}_has_set')
        if (not has_set) or reload:
            # print('if (not has_set) or reload:', has_set, reload)
            self._load()

    def _load(self):
        # print('ProxyRotator self.filtres', self.filtres)
        protocol_raw = self.filtres.pop('protocol')
        query = self.db.query(ProxyModel).filter_by(**self.filtres)
        if not self.use_postponed:
            query = query.filter(ProxyModel.use_postponed_to < datetime.now())

        if protocol_raw !='all':
            protocol_list = protocol_raw.split(',')
            query = query.filter(ProxyModel.protocol.in_(protocol_list))

        proxy_list = query.all()

        # print('proxy_list\n', proxy_list)

        # proxy_list = self.db.query(ProxyModel).\
        #         filter_by(**self.filtres).\
        #         filter(ProxyModel.use_postponed_to < datetime.now()).\
        #         filter(ProxyModel.protocol.id.in_(protocol_list)).\
        #         all()

        proxy_list = [str(el) for el in proxy_list]
        curr_list = self.get_proxy_list()

        curr = set(curr_list)
        inp = set(proxy_list)
        diff = list(inp - curr)
        if diff:
            self.rdb.lpush(f'{self.prefix}_proxy_list', *diff)
            self.rdb.set(f'{self.prefix}_has_set', 1)

    def reload(self,use_postponed=False, **filtres):
        self.use_postponed = use_postponed
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


def proxy_url_to_dict(proxy_url):
    out = {'url':proxy_url}
    stage1 = proxy_url.split('://')
    out['protocol'] = stage1[0]
    # if out['protocol'] == 'socks':
    #     out['protocol'] = 'socks4'
    stage2 = stage1[-1].split('@')
    if len(stage2) > 1:
        name_pass = stage2[0].split(':')
        out['user'] = name_pass[0]
        out['password'] = name_pass[1]

    addr_port = stage2[-1].split(':')
    out['host'] = addr_port[0]
    out['port'] = addr_port[1]
    return out






class OptionsMaker(object):
    def __init_(self):
        pass

    def get_chrome_proxy_extensions(self, proxy):
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """

        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                  singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                }
              };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (proxy['host'], proxy['port'], proxy['user'], proxy['password'])

        temp_dir = pathlib.Path(gettempdir())
        pluginfile = f'{temp_dir / str(uuid.uuid1())}.zip'

        chrome_options = webdriver.ChromeOptions()

        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)

        chrome_options.add_extension(pluginfile)
        extensions = chrome_options.extensions
        del chrome_options
        os.remove(pluginfile)
        return extensions


    def chrome(self, proxy_url=None, user_agent=None):
        # "http", "https", "quic", "socks4","socks5"
        capabilities = {
            "browserName": "chrome",
            "version": "81.0",
            "enableVNC": True,
            "enableVideo": False,
        }
        options = {"extensions": [], "args":[]}
        if proxy_url:
            logger.info(f'use proxy: {proxy_url}')
            proxy = proxy_url_to_dict(proxy_url)
            if 'user' in proxy:
                options["extensions"] = self.get_chrome_proxy_extensions(proxy)
            else:
                options["args"].append(f"--proxy-server={proxy_url}")

        if user_agent:
            options["args"].append(f"--user-agent={user_agent}")





        capabilities["goog:chromeOptions"] = options

        return capabilities



STATUS_CODE_LIST = {
    'title':[r'404',r'500'],
    'net': [
        r'DNS_PROBE_FINISHED_NXDOMAIN',
        r'ERR_NAME_NOT_RESOLVED',
        r'ERR_CONNECTION_TIMED_OUT',
        r'ERR_TIMED_OUT',
        r'ERR_PROXY_CONNECTION_FAILED',
        r'ERR_CERT_COMMON_NAME_INVALID'
    ],
    'captcha':[
        r'META NAME=\"ROBOTS\"',
        r'hcaptcha'
        ]
}



class ChromeDriverBoot(object):
    def __init__(self):
        self.proxy_rotator = ProxyRotator()
        self.agent_rotator = UserAgent()

    def try_connect(self, start_url, use_proxy, use_agent):
        param = {} #'198.27.76.4:5007' #
        if use_proxy:
            proxy_url = self.proxy_rotator.next()
            # print('-------- use proxy', proxy_url)
            param['proxy_url'] = proxy_url

        if use_agent:
            param['user_agent'] = self.agent_rotator.random


        driver = webdriver.Remote(
            command_executor = SELENOID_HUB,
            desired_capabilities = OptionsMaker().chrome(**param))
        driver.get(start_url)
        return driver, param



    def proc_captcha(self, driver):
        for _ in range(360):
            stat = get_status(driver)
            if stat=='OK':
                return driver
            elif stat in STATUS_CODE_LIST.get('captcha'):
                time.sleep(1)

        raise Exception('Could not solve captcha')





    def get(self, start_url, use_proxy=True, use_agent=False):

        for i in range(UPLOAD_NEW_PROXIES_IF_LESS_THAN):
            driver, param = self.try_connect(start_url, use_proxy, use_agent)
            stat = get_status(driver)
            logger.info(f'get {start_url} try:{i} status: {stat}')

            if stat=='OK':
                return driver

            elif stat in ['ERR_CONNECTION_TIMED_OUT','ERR_TIMED_OUT', 'ERR_PROXY_CONNECTION_FAILED']:
                if param.get('proxy_url'):
                    self.proxy_rotator.delete( param.get('proxy_url'),
                        f'Connection refused: proxy deleted, target {start_url}')
                else:
                    raise Exception('ERR_CONNECTION_TIMED_OUT')
            elif stat in STATUS_CODE_LIST.get('captcha'):
                logger.warnind('\n\n ============= Please solve the captcha =========\n\n')
                return self.proc_captcha(driver)



def get_status(driver):

    try:
        result = []
        for stat_key in STATUS_CODE_LIST:
            if stat_key=='title':
                result.extend(re.findall(r'|'.join(STATUS_CODE_LIST.get(stat_key)),
                                                                driver.title))
            else:
                result.extend(re.findall(r'|'.join(STATUS_CODE_LIST.get(stat_key)),
                                                            driver.page_source))

        return result[0] if result else 'OK'

    except Exception as e:
        logger.error(traceback.format_exc(ERROR_TRACE_LEVEL))
        return 'ERR_CONNECTION_TIMED_OUT'
