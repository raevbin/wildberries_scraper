# -*- coding: utf-8 -*-
import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst


def clear_price(text):
    text = text.replace(u'\u00a0', '')
    text = text.replace(u'\u20bd', '')
    return text


class WildsearchCrawlerItemWildberries(scrapy.Item):

    instock = scrapy.Field(
        output_processor=TakeFirst()
    )

    category_id = scrapy.Field(
        output_processor=TakeFirst()
    )

    parse_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    marketplace = scrapy.Field(
        output_processor=TakeFirst()
    )
    product_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    product_name = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    image_urls = scrapy.Field()
    wb_id = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_parent_id = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_category_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_category_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_category_position = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_reviews_count = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_purchases_count = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_price = scrapy.Field(
        input_processor=MapCompose(str.strip, clear_price),
        output_processor=TakeFirst()
    )
    wb_rating = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_brand_name = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_brand_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_brand_country = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_manufacture_country = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst()
    )
    wb_first_review_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_last_review_date = scrapy.Field(
        output_processor=TakeFirst()
    )

class WildsearchCrawlerItemWildberriesCategory(scrapy.Item):
    parse_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    marketplace = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_category_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_category_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    wb_category_level = scrapy.Field(
        output_processor=TakeFirst()
    )


class WildsearchCrawlerItemProductcenterProducer(scrapy.Item):


    parse_date = scrapy.Field(
        output_processor=TakeFirst()
    )
    marketplace = scrapy.Field(
        output_processor=TakeFirst()
    )
    category_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    category_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_name = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_about = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_address = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_coords = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_distance = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_phone = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_email = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_website = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_goods_count = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_logo = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_rating = scrapy.Field(
        output_processor=TakeFirst()
    )
    producer_price_lists = scrapy.Field()
