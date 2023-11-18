from scrapy.crawler import CrawlerProcess
from scraper.carousellSpider import CarousellSpider

class CarousellScraper():

    def __init__(self, search_terms):
        self.search_terms = search_terms
    
    def start(self):
        process = CrawlerProcess(settings = {
            'USER_AGENT': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0',
        })

        spider = CarousellSpider
        spider.search_terms = self.search_terms
        process.crawl(spider)
        process.start()