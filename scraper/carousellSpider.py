from config.definitions import ROOT_DIR
from scraper.carousellResponseParser import CarousellResponseParser
import scrapy
import csv
import os

class CarousellRequest(scrapy.Request):
    search_term = ''

class CarousellSpider(scrapy.Spider):
    name = "carousell"
    search_terms = []

    def start_requests(self):
        for search_term in self.search_terms:
            url = f'https://www.carousell.sg/search/{search_term.replace(" ", "%20")}?addRecent=false&canChangeKeyword=true&includeSuggestions=false&t-search_query_source=direct_search&tab=marketplace'
            request = CarousellRequest(url=url, callback=self.parse)
            request.search_term = search_term
            yield request

    def parse(self, response):
        item_list = CarousellResponseParser(response).parse()

        csv_file_path = os.path.join(ROOT_DIR, "data", f'{response.request.search_term.replace(" ", "_")}.csv')

        with open(csv_file_path, 'w', newline='') as csv_file:
            # Extract the fieldnames from the keys of the first dictionary in the array
            fieldnames = item_list[0].keys()

            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write the header to the CSV file
            csv_writer.writeheader()

            csv_writer.writerows(item_list)

