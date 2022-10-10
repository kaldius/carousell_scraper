import csv
from config.definitions import ROOT_DIR
from scraper import scraper
import os
import json


def extract_all_search_terms(monitored_searches):
    search_terms = []
    for user_id in monitored_searches:
        for search_term in monitored_searches[user_id]["searches"]:
            search_terms.append(search_term)
    return search_terms


if __name__ == "__main__":
    load_path = os.path.join(ROOT_DIR, "data", "monitored_searches.json")
    if os.path.exists(load_path):
        with open(load_path, "r", encoding="utf-8") as f:
            monitored_searches = json.load(f)
            print(monitored_searches)
            all_search_terms = extract_all_search_terms(monitored_searches)
            for item in all_search_terms:
                print("\nScraping for: " + item)
                scraper.search(item, all_search_terms[item]["exclude"])
