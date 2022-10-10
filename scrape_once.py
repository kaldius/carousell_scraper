import csv
from config.definitions import ROOT_DIR
from scraper import scraper
import os
import json


def extract_all_search_items(monitored_searches):
    # search_items is a list of tuples (query, exclude) [note that exclude is a list]
    search_items = []
    for user_id in monitored_searches:
        for search_term in monitored_searches[user_id]["searches"]:
            search_items.append(
                (
                    search_term,
                    monitored_searches[user_id]["searches"][search_term]["exclude"],
                )
            )
    return search_items


if __name__ == "__main__":
    load_path = os.path.join(ROOT_DIR, "data", "monitored_searches.json")
    if os.path.exists(load_path):
        with open(load_path, "r", encoding="utf-8") as f:
            monitored_searches = json.load(f)
            print(monitored_searches)
            all_search_terms = extract_all_search_items(monitored_searches)
            for search_term, exclude in all_search_terms:
                print("\nScraping for: " + search_term)
                scraper.search(search_term, exclude)
