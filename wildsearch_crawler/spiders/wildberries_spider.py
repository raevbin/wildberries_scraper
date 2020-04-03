import datetime
import logging
import scrapy
import re
from pprint import pprint
from .base_spider import BaseSpider
from scrapy.loader import ItemLoader
from wildsearch_crawler.items import WildsearchCrawlerItemWildberries
from wildsearch_crawler.db import Session, CatalogModel, ItemModel
from wildsearch_crawler.db import get_catalog_endpoints, get_elements_by_id

logger = logging.getLogger('main')


class WildberriesSpider(BaseSpider):
    name = "wb"
    limit = None


    def start_requests(self):

        item_ids = getattr(self, 'item_ids', None)
        self.limit = getattr(self, 'limit', None)

        if item_ids:
            self.skip_variants = True
            for i, el in enumerate(get_elements_by_id(item_ids, ItemModel)):
                # print('url', el)
                if i == self.limit:
                    return
                yield scrapy.Request(el.url, self.parse_good)

            return


        catalog_ids = getattr(self, 'catalog_ids', None) # <number>, <range>, all, endpoints

        if catalog_ids:
            objects = []
            if catalog_ids == 'endpoints':
                objects = get_catalog_endpoints()
            else:
                objects = get_elements_by_id(catalog_ids, CatalogModel)


            for i, el in enumerate(objects):
                if i == self.limit:
                    return
                yield scrapy.Request(el.url, self.parse_category, cb_kwargs={'category_id': el.id})

            return


    def parse(self, response):
        pass

    def start_parse_by_category_ids(self, item_ids_raw):
        pass

    def parse_sitemap(self, response):
        for url in response.css('#sitemap a::attr(href)'):
            yield response.follow(url, self.parse_category)

    def parse_category(self, response, category_id):
        logger.info(f'parse_category {response}')

        def clear_url_params(url):
            return url.split('?')[0]

        def parse_id_from_url(url):
            return url.split('/')[4]

        wb_category_position = int(response.meta['current_position']) if 'current_position' in response.meta else 1
        wb_category_url = clear_url_params(response.url)
        wb_category_name = response.css('h1::text').get()

        allow_dupes =  getattr(self, 'allow_dupes', False)
        skip_details = getattr(self, 'skip_details', False)

        # follow links to goods pages
        for item in response.css('.catalog-content .j-card-item'):

            logger.info(f'>>> parse item {item}')
            good_url = item.css('a.ref_goods_n_p::attr(href)')

            if skip_details:
                # ItemLoader выключен в угоду скорости
                '''
                current_good_item = WildsearchCrawlerItemWildberries()
                loader = ItemLoader(item=current_good_item, response=response)

                loader.add_value('wb_id', parse_id_from_url(good_url.get()))
                loader.add_value('product_name', item.css('.goods-name::text').get())
                loader.add_value('parse_date', datetime.datetime.now().isoformat(" "))
                loader.add_value('marketplace', 'wildberries')
                loader.add_value('product_url', clear_url_params(good_url.get()))
                loader.add_value('wb_category_url', wb_category_url)
                loader.add_value('wb_category_position', wb_category_position)
                loader.add_value('wb_brand_name', item.css('.brand-name::text').get())

                yield loader.load_item()
                '''

                yield {
                    'wb_id': datetime.datetime.now().isoformat(" "),
                    'product_name': item.css('.goods-name::text').get(),
                    'wb_reviews_count': item.css('.dtList-comments-count::text').get(),
                    'wb_price': item.css('.lower-price::text').get().replace(u'\u20bd', '').replace(u'\u00a0', ''),
                    'parse_date': datetime.datetime.now().isoformat(" "),
                    'marketplace': 'wildberries',
                    'product_url': clear_url_params(good_url.get()),
                    'wb_category_url': wb_category_url,
                    'wb_category_name': wb_category_name,
                    'wb_category_position': wb_category_position,
                    'wb_brand_name': item.css('.brand-name::text').get().strip()
                }
            else:
                yield response.follow(clear_url_params(good_url.get()), self.parse_good, dont_filter=allow_dupes, meta={
                    'current_position': wb_category_position,
                    'category_url': wb_category_url,
                    'category_name': wb_category_name
                },
                cb_kwargs={'category_id': category_id})

            wb_category_position += 1

        # follow pagination


        # for a in response.css('.pager-bottom a.next'):
        #     yield response.follow(a, callback=self.parse_category, meta={'current_position': wb_category_position})

    def parse_good(self, response, category_id=None):

        logger.info(f'parse good {response.url} ')



        def clear_url_params(url):
            return url.split('?')[0]

        def generate_reviews_link(base_url, sort='Asc'):
            # at first it is like https://www.wildberries.ru/catalog/8685970/detail.aspx
            # must be like https://www.wildberries.ru/catalog/8685970/otzyvy?field=Date&order=Asc
            link_param = response.css('#Comments a.show-more::attr(data-link)').get()

            return re.sub('detail\.aspx.*$', f'otzyvy?field=Date&order={sort}&link={link_param}', base_url)

        skip_images = getattr(self, 'skip_images', False)
        skip_variants = getattr(self, 'skip_variants', False)
        allow_dupes = getattr(self, 'allow_dupes', False)

        current_good_item = WildsearchCrawlerItemWildberries()
        parent_item = response.meta['parent_item'] if 'parent_item' in response.meta else None

        loader = ItemLoader(item=current_good_item, response=response)

        # category position stats
        wb_category_url = response.meta['category_url'] if 'category_url' in response.meta else None
        wb_category_name = response.meta['category_name'] if 'category_name' in response.meta else None
        wb_category_position = response.meta['current_position'] if 'current_position' in response.meta else None

        canonical_url = response.css('link[rel=canonical]::attr(href)').get()


        # logger.info(f'>>>> wb_category_url:  {wb_category_url}')
        if canonical_url != response.url:
            yield response.follow(clear_url_params(canonical_url), self.parse_good, dont_filter=allow_dupes,  meta={
                'current_position': wb_category_position,
                'category_url': wb_category_url
            }, cb_kwargs={'category_id': category_id})

            return

        # scraping brand and manufacturer countries
        wb_brand_country = ''
        wb_manufacture_country = ''

        for param in (response.css('.params .pp')):
            param_name = param.css('span:nth-of-type(1) b::text').get()
            param_value = param.css('span:nth-of-type(2)::text').get()

            if u'Страна бренда' == param_name:
                wb_brand_country = param_value

            if u'Страна производитель' == param_name:
                wb_manufacture_country = param_value

        # fill css selectors fields
        loader.add_css('product_name', '.brand-and-name .name::text')
        loader.add_css('wb_reviews_count', '.count-review i::text')
        loader.add_css('wb_price', '.final-cost::text')
        loader.add_css('wb_rating', '.product-rating span::text')
        loader.add_css('wb_id', 'div.article span::text')

        # fill non-css values
        loader.add_value('instock', False if len(response.css('.j-price.order-block.hide')) else True )

        loader.add_value('parse_date', datetime.datetime.now().isoformat(" "))
        loader.add_value('marketplace', 'wildberries')
        loader.add_value('product_url', response.url)
        loader.add_value('wb_brand_name', response.css('.brand-and-name .brand::text').get())
        loader.add_value('wb_brand_url', response.css('.brandBannerImgRef::attr(href)').get())
        loader.add_value('wb_brand_country', wb_brand_country)
        loader.add_value('wb_manufacture_country', wb_manufacture_country)
        loader.add_value('wb_category_url', wb_category_url)
        loader.add_value('wb_category_name', wb_category_name)
        loader.add_value('wb_category_position', wb_category_position)
        loader.add_value('category_id', category_id)




        # create list of images
        if skip_images is False:
            image_urls = []

            for tm in (response.css('.pv-carousel .carousel a img::attr(src)')):
                image_urls.append(tm.get().strip().replace('tm', 'big'))

            loader.add_value('image_urls', image_urls)

        # fill purchase count in inline json
        # "ordersCount":1100,
        curren_id = loader.load_item().get('wb_id')
        loader.add_value('wb_purchases_count', re.compile(f'{curren_id},\"ordersCount\":(\d+),').search(response.text)[1])


        # logger.info(f'parent_item >>>> \n\n\n {parent_item}  \n\n\n')
        if parent_item is not None:
            loader.add_value('wb_parent_id', parent_item.get('wb_id', ''))

        # get reviews dates
        yield response.follow(generate_reviews_link(response.url, 'Asc'), callback=self.parse_good_first_review_date, errback=self.parse_good_errback, meta={'loader': loader}, headers={'x-requested-with': 'XMLHttpRequest'})

        # follow goods variants only if we scrap parent item
        if skip_variants is False and parent_item is None:
            for variant in (response.css('.options ul li a::attr(href)')):
                yield response.follow(clear_url_params(variant.get()), callback=self.parse_good, meta={
                    'parent_item': loader.load_item() #current_good_item
                }, cb_kwargs={'category_id': category_id})

    def parse_good_first_review_date(self, response):
        if len(response.css('.comment')) > 0:
            response.meta['loader'].add_value('wb_first_review_date', response.css('.comment')[0].css('.time::attr(content)').get())

        yield response.meta['loader'].load_item()

    def parse_good_errback(self, response):
        yield response.meta['loader'].load_item()
