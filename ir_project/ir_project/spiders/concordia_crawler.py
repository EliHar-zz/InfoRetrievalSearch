import re
from boilerpipe.extract import Extractor
from ir_project.items import IrProjectItem
from goose import Goose
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

class ConcordiaCrawlerSpider(CrawlSpider):
    name = "concordia_crawler"

    allowed_domains = ["concordia.ca"]
    start_urls = ["http://www.concordia.ca/artsci/science-college.html"]
    
    rules = (
        Rule(LinkExtractor(allow=('/artsci/science-college/*', )),callback='parse_item', follow=True),
    )

    def parse_item(self, response):
        item = IrProjectItem()
        g = Goose()
        content = g.extract(url = response.url)

        item['url'] = response.url

    	item['title'] = content.title

    	extractor = Extractor(extractor = 'ArticleExtractor', url = response.url)

    	body = extractor.getText().replace('\n',' ')

    	item['body'] = re.sub(r'[^\x00-\x7F]+', ' ', body)
        
        return item
