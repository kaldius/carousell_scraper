from bs4 import BeautifulSoup
from numpy import save
import requests
import re
import pandas as pd
import os
from config.definitions import ROOT_DIR, CAROUSELL_URL

# creates BeautifulSoup object from html
def request_page(url):
    html_text = requests.get(url).text
    return BeautifulSoup(html_text, "lxml")


def get_items(query: str):
    page_count = 1
    item_list = []
    extension = "/search/" + query.replace(" ", "%20")

    while extension != None:
        item_count = 0
        soup = request_page(CAROUSELL_URL + extension)
        all_items = soup.main.find_all(
            attrs={"data-testid": re.compile("listing-card-\d{10}")}
        )
        print("Number of items: ", len(all_items), "Page: ", page_count)
        print("URL: ", CAROUSELL_URL + extension)

        for item in all_items:
            item_attributes = {}

            # Retrieve data from website using HTML tags
            # TODO: possible improvement: add filters here to stop scraping item once it fails
            listing_url_tag = item.find(
                href=re.compile("/p/")
            )  # will be using relative positions from this tag to find other data
            item_attributes["listing_url"] = listing_url_tag.get("href")
            item_attributes["title"] = listing_url_tag.next_element.next_sibling.text
            item_attributes[
                "price"
            ] = listing_url_tag.next_element.next_sibling.next_sibling.find("p").text
            item_attributes["seller_url"] = item.find(href=re.compile("/u/")).get(
                "href"
            )
            item_attributes["age"] = item.find(
                attrs={"data-testid": "listing-card-text-seller-name"}
            ).next_sibling.text

            # append the item to the list
            item_list.append(item_attributes)

            item_count += 1

        print("Number of items scraped: ", item_count)
        print("-" * 40)

        # Retrieve new extension (next extension is for the Next page) THIS DOESN'T WORK ATM
        # TODO: find a new way to get the next page (Selenium?)
        extension = soup.find("li", class_="pagination-next pagination-btn")
        if extension != None:
            extension = extension.select("a")[0].get("href")

        page_count += 1
        # time.sleep(5)

    return item_list


def process_and_save(item_list: dict, query: str):
    df = pd.DataFrame(item_list)

    # define col order
    cols = ["title", "price", "age", "seller_url", "listing_url"]
    df = df[cols]

    # clean up columns
    df["price"] = (
        df["price"]
        .str.replace("FREE", "0")
        .str.replace("S$", "", regex=False)
        .str.replace(",", "")
        .astype(float)
    )
    df["age"] = df["age"].str.replace(" ago", "", regex=False)

    # sort by age
    df.sort_values(by="age", key=age_series_str_to_hours, inplace=True)

    save_path = os.path.join(ROOT_DIR, "data")

    if not os.path.exists(save_path):
        os.mkdir(save_path)

    df.to_csv(
        save_path + "/" + query.replace(" ", "_") + ".csv",
        index=False,
    )


# convert age string to hours (for sorting)
def age_series_str_to_hours(age_series):
    output = []
    for age in age_series:
        age_split = age.split(" ")
        number = int(age_split[0])
        if "min" in age_split[1]:
            output.append(number / 60)
        elif "hour" in age_split[1]:
            output.append(number)
        elif "day" in age_split[1]:
            output.append(number * 24)
        elif "month" in age_split[1]:
            output.append(number * 24 * 30)
        elif "year" in age_split[1]:
            output.append(number * 24 * 30 * 12)
        else:
            output.append(0)
    return output


def new_search(query: str):
    item_list = get_items(query)
    process_and_save(item_list, query)
