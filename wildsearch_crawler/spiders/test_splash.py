import scrapy
from scrapy_splash import SplashRequest
import logging
from pprint import pprint
from urllib.parse import urlencode
from fake_useragent import UserAgent
user_agent = UserAgent()

logger = logging.getLogger('main')


# js_script = '''
#   window.step = function() {
#     var num = localStorage.getItem('step');
#     if (num) {
#       num = Number(num);
#     }else{
#       num = 0;
#     }
#     num = num + 1;
#     localStorage.setItem('step', num);
#     return num
#   }
# '''

js_script = """
window.step = function() {}
"""


#   window.manage = function (){
#     var current_step = step();
#     switch (current_step) {
#       case 1:
#         set_urban();
#         break;
#       case 2:
#         set_id();
#         set_plot();
#         click_search();
#         break;
#       case 3:
#         break;
#       default:
#     }
#   }
#
#   window.set_urban = function(){
#     var sel_urban = $('.ms-formbody select').eq(0);
#     var option = sel_urban.find('option').eq(1);
#     option.attr('selected','selected');
#     sel_urban.change();
#   }
#
#   window.set_id = function() {
#     var sel_id = $('.ms-formbody select').eq(1);
#     var option = sel_id.find('option').eq(1);
#     option.attr('selected','selected');
#     sel_id.change();
#   }
#
#   window.set_plot = function() {
#     var inp_plot = $('.ms-formbody input[type="text"]');
#     inp_plot.val(1);
#   }
#
#   window.click_search = function() {
#     var inp_search = $('.ms-formbody input[value="Search"]');
#     inp_search.click();
#   }
#
#   window.reset = function() {
#     localStorage.removeItem('step');
#   }
# '''


lua_script = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method

    })
  assert(splash:wait(2))

  local entries = splash:history()
  local last_response = entries[#entries].response


  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),

  }
end
"""
# % js_script
 #    result = result
 # local result = splash:runjs("step()")
  # assert(splash:runjs("%s"))
lua_script_ = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(2))

  local entries = splash:history()
  local last_response = entries[#entries].response


  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),

  }
end
"""



#
  #
#
lua_script = """
function main(splash)
    assert(splash:go(splash.args.url))
    return {result=0}
end
"""




class MySpider(scrapy.Spider):

    name = 'test_splash'
    start_urls = [
                "https://www.hsvphry.org.in/Pages/PlotStatusEnquiry.aspx"
                ]

    def start_requests(self):
        print('start_requests >>>  ')
#
        for url in self.start_urls:
            print(f'parse url >> {url}')
            try:
                yield SplashRequest(url, self.parse,
                                        # args={'wait': 10},
                                        # endpoint='render.json',
                                        endpoint='execute',
                                        session_id=1,
                                        # headers={
                                        #     'User-Agent': user_agent.random
                                        # },
                                        cache_args=['lua_source'],
                                        args={
                                                'lua_source': lua_script,
                                                'wait': 2},
                                        # headers={'X-My-Header': 'value'},
                                        )
            except Exception as e:
                print('Exception',e)
                raise


    def parse(self, response):
        print('response',response)
        # logger.info('\n\n\n\n table[cellspacing] tbody tr th')
        # logger.info(response.css('table[cellspacing] tbody tr th'))
        # logger.info('\nhtml\n')
        # logger.info(response.html)
        return {}
