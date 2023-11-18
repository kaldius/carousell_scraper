from config.definitions import ROOT_DIR
from scraper.carousellScraper import CarousellScraper
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

            # TODO: deal with exclude terms
            # all_search_terms is an array of pairs: (search_term, exclude)

            search_terms = [pair[0] for pair in all_search_terms]
            scraper = CarousellScraper(search_terms=search_terms)
            scraper.start()
