import csv
from config.definitions import ROOT_DIR
from scraper import scraper
import os

if __name__ == "__main__":
    load_path = os.path.join(ROOT_DIR, "data", "monitored_searches.csv")
    if os.path.exists(load_path):
        with open(load_path, "r") as f:
            reader = csv.reader(f)
            monitored_searches = {int(row[0]): row[1:] for row in reader}
            for list_of_items in monitored_searches.values():
                for item in list_of_items:
                    scraper.search(item)
