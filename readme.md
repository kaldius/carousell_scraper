# Carousell Scraper
A web scraper for [Carousell](https://www.carousell.sg) which uses [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) for scraping and [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for front-end user interaction.

## Quick Start
1. Create a `token.txt` file in the `config` directory of this package and paste your token in the file **without** any whitespaces/newlines.
2. Install python dependencies.
```
# optional
python -m venv my_venv
source my_venv/bin/activate

pip install -r requirements.txt
```
3. Run `main.py` to start the telegram bot.
```
python main.py
```
4. Create script to run regularly with crontab. It should include:
```
#!/usr/bin/env bash

source <path_to_venv>/bin/activate
python <path_to_this_repo>/scrape_once.py
```
5. Create a crontab task to automate the running of your script. Use `crontab -e` to access the crontab file and add a new line to run your script as often as you like!


## `main.py`
---
### `get_items(query)`
Scrapes Carousell for search results related to query string.

**Parameters**: 
* query: str
    
    String to search for on Carousell

**Returns**: List

* Each list item is a dictionary representing a listing, with the following keys:
    * title
    * price
    * age
    * seller_link
    * listing_link

### `process_and_save(item_list, query)`
Processes scraped data and saves it in `/data/`.

**Parameters**:
* item_list: list
    The output of [`get_items`](#getitemsquery)
* query: str
    Same as input of [`get_items`](#getitemsquery)

**Returns**: None


## `stonksDeal_bot.py`
---
Available commands:
* `/start`: Just replies with "I'm a bot, please talk to me!" for now.
* `/recent`: Displays the most recently posted listing in the latest scrape. Optional: specify number of listings to show
> e.g. "/recent 5" shows the 5 most recently posted listings
* `/cheapest`: Displays the cheapest listing in the latest scrape. Optional: specify number of listings to show
> e.g. "/cheapest 5" shows the 5 cheapest listings
* `/range`: Displays all listings with price in the given range. Compulsary: two integers for max and min respectively
> e.g. "/range 20 30" shows all listings with price between S$20 to S$30
* `/add`: Adds a search term to the currently monitored searches and calls for the scraper to do an initial scrape. This automatically sets the new search term to be the user's latest **selection**
> e.g. "/add ipad mini" adds the search term "ipad mini" to the currently monitored list
* `/switch`: Presents a list of buttons for the user to make a **selection** on which to make queries
> e.g. after **selection** is set to "ipad mini", "/recent 2" will show the 2 most recently posted listings for "ipad mini"


## Learning Points
1. BeautifulSoup
    * `.find_all()` searches for all html tags that meet the given conditions. **Tip**: use a dictionary to specify conditions. e.g.:
    >`soup.main.find_all(attrs={"data-testid": re.compile("listing-card-\d{10}")})`
    * class names are one of the most common ways to identify an element
    * some websites (like carousell) regularly change class names (WHY!?) so the above might not always be the best way
    * [`.next_sibling`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#going-sideways) and [`.next_element`](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#going-back-and-forth) are **very** useful for traversing the DOM tree if the desired item is near another one that is already identified
2. Telegram Bot
    * You will first need an Access Token from the @BotFather bot
    * General idea:
        1. Write callback function
        2. Create handler
        3. Add handler to dispatcher
    * To add an [InlineKeyboard](https://github.com/python-telegram-bot/python-telegram-bot/wiki/InlineKeyboard-Example):
        1. Create a **double** nested list of `InlineKeyboardButton`
        2. Pass the keyboard list to `InlineKeyboardMarkup`
        3. Set `reply_markup` parameter for message reply to the above keyboard markup
        4. Create a callback for button presses and use it to create a `CallbackQueryHandler`
3. Crontab
    * Use `crontab -e` to edit your user's crontab or `sudo vim /etc/crontab` to edit.
    * Format is relatively simple, just read the crontab file.
    * **Tip**: use `0,15,30,45` in the minutes field to run the command at the respective mins, OR you can use `/15` to run every 15 mins, though not necessarily at the 0th, 15th, 30th and 45th minutes.


Todo(bot side):
- [ ] Beautify format of output (currently so ugly its unusable) [consider cards with images? and maybe show only a few(3) and allow user to click to show more]
    - [x] make it not ugly
    - [ ] Images?
    - [ ] how to not spam user with all 5
    - [ ] click to show more listings?
- [x] Make `/add` command to scrape for new search term
    - [x] global variable to store current query to use the other functions
    - [x] make `/switch` command to switch to other tracked items
- [ ] Check for diffs at each new scrape and automatically push them to user
    - [ ] add command to subscribe/unsubscribe to this
- [ ] notifications when new listings are added
- [ ] add error callback

Todo(scraper side):
- [x] maintain list of tracked search terms
- [ ] scheduled scraping
- [ ] diffs between scrapes
    - [ ] how to see diffs? since the age of the item changes with each scrape. Look for items with age < scraping interval?
- [ ] store user bookmarks or already viewed listings