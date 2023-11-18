from bs4 import BeautifulSoup
import re

class CarousellResponseParser():

    def __init__(self, response):
        self.soup = BeautifulSoup(response.text, "lxml")

    # returns a list of item_attribute dicts
    def parse(self):
        all_items = self.soup.main.find_all(
            attrs={"data-testid": re.compile("listing-card-\d{10}")}
        )
        item_list = []
        for item in all_items:
            item_attributes = CarousellItemParser(item).parse()
            if item_attributes is not None:
                item_list.append(item_attributes)
        
        # sort by age
        return sorted(item_list,
                      key=CarousellResponseParser.age_key_function)

    def age_key_function(item_attribute):
        return CarousellResponseParser.age_str_to_hours(item_attribute['age'])

    # convert age string to hours (for sorting)
    def age_str_to_hours(age_str):
        split_age = age_str.split(" ")
        number = int(split_age[0])
        if "min" in split_age[1]:
            return number / 60
        elif "hour" in split_age[1]:
            return number
        elif "day" in split_age[1]:
            return number * 24
        elif "month" in split_age[1]:
            return number * 24 * 30
        elif "year" in split_age[1]:
            return number * 24 * 30 * 12
        else:
            return 0

class CarousellItemParser:

    # TODO: implement excluded words
    def __init__(self, item):
        self.item = item
    
    def parse(self):
        item_attributes = {
            "listing_url": self.get_listing_url(),
            "title": self.get_title(),
            "price": self.get_price(),
            "stricken_price": self.get_stricken_price(),
            "seller_url": self.get_seller_url(),
            "age": self.get_age(),
            "is_bumped": self.is_bumped(),
        }

        return item_attributes

    def get_listing_url(self):
        try:
            return self.item.find(
                href=re.compile("/p/")
            ).get("href")
        except:
            return None

    def get_title(self):
        try:
            return self.item.find(
                href=re.compile("/p/")
            ).next_element.next_sibling.text  
        except:
            return None

    def get_price(self):
        try:
            price = self.item.find(
                href=re.compile("/p/")
            ).next_element.next_sibling.next_sibling.find('p').text  
            return CarousellItemParser.price_string_to_float(price)
        except:
            return None

    def get_stricken_price(self):
        try:
            # if the element does not exist, stricken_price should be None
            stricken_price_element = self.item.find(
                href=re.compile("/p/")
            ).next_element.next_sibling.next_sibling.find('s')
            if stricken_price_element is None:
                return None
            return CarousellItemParser.price_string_to_float(stricken_price_element.text)
        except:
            return None

    def price_string_to_float(price):
        return float(price.replace('FREE', '0') \
                          .replace('S$', "") \
                          .replace(",", ""))

    def get_seller_url(self):
        try:
            return self.item.find(href=re.compile("/u/")).get("href")
        except:
            return None
    
    def get_age(self):
        try:
            age = self.item.find(
                attrs={"data-testid": "listing-card-text-seller-name"}
            ).next_sibling.text

            return age.replace(" ago", "")
        except:
            return None

    def is_bumped(self):
        try:
            return (
                self.item.find(
                    attrs={"data-testid": "listing-card-text-seller-name"}
                ).next_sibling.find("svg")
                != None
            )
        except:
            return None
