import json
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import pandas as pd
import os
import math
from config.definitions import ROOT_DIR, CAROUSELL_URL, TOKEN_DIR
from multiprocessing.connection import Listener

monitored_searches = {}
"""
monitored searches format:
{
  <user_id1>: {
    "searches": {
      <search_term>: {
        "max_price": <max_price>,
        "min_price": <min_price>,
        "exclude" : <exclude_array>,
      },
    }
  }
  <user_id2>: {
    "searches": {
      <search_term>: {
        "max_price": <max_price>,
        "min_price": <min_price>,
        "exclude" : <exclude_array>,
      },
    }
  }
}
"""


load_path = os.path.join(ROOT_DIR, "data", "monitored_searches.json")

if os.path.exists(load_path):
    with open(load_path, "r", encoding="utf-8") as f:
        monitored_searches = json.load(f)
        print(monitored_searches)
else:
    print("No monitored searches file found, creating new one.")


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    welcome_text = "Welcome to _*StonksDealFinder\!*_\
\nThis bot will help you find stonks deals on Carousell\.\n\n\
To get started, add a search term using the /add command\.\n\n\
You can then use the /recent and /cheapest commands to find\
the most *recent* or *cheapest* listings\.\n e\.g\. \`recent 5\` displays \
the 5 most recent listings related to your currently selected \
search term\.\n\nTo switch between your searches, use the /switch command\.\n"
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=welcome_text, parse_mode="MarkdownV2"
    )


# formatting output to look nice in telegram
def format_message(series: pd.Series):
    """
    Format a pandas Series as a string.
    """
    return (
        "["
        + series["title"]
        + "]("
        + CAROUSELL_URL
        + series["listing_url"]
        + ")"
        + ": S$"
        + series["price"].astype(str)
        + "\n Listed "
        + series["age"]
        + " ago by "
        + "["
        + series["seller_url"][3:-1]
        + "]("
        + CAROUSELL_URL
        + series["seller_url"]
        + ")"
    )


# show the 'num' most recently posted listings in latest scrape
def recent(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        num = 1
    elif len(context.args) != 1 or not context.args[0][:].isdigit():
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /recent OR /recent <int>",
        )
        return
    else:
        num = int(context.args[0])

    if "selection" not in context.user_data:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please select a search term first. Hint: /switch",
        )
        return

    selected_search = context.user_data["selection"]
    with open(
        ROOT_DIR + "/data/" + selected_search.replace(" ", "_") + ".csv", "r"
    ) as f:
        df = pd.read_csv(f)
        for i in range(num):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=format_message(df.iloc[i]),
                parse_mode="Markdown",
            )


# show the 'num' cheapest listings in latest scrape
def cheapest(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        num = 1
    elif len(context.args) > 1 or not context.args[0][:].isdigit():
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /cheapest OR /cheapest <int>",
        )
        return
    else:
        num = int(context.args[0])

    if "selection" not in context.user_data:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please select a search term first. Hint: /switch",
        )
        return

    selected_search = context.user_data["selection"]
    with open(
        ROOT_DIR + "/data/" + selected_search.replace(" ", "_") + ".csv", "r"
    ) as f:
        df = pd.read_csv(f).nsmallest(num, "price")
        for i in range(num):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=format_message(df.iloc[i]),
                parse_mode="Markdown",
            )


# show all listings within range a, b
def price_range(update: Update, context: CallbackContext):
    if (
        len(context.args) != 2
        or not context.args[0][:].isdigit()
        or not context.args[1][:].isdigit()
    ):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /range <int> <int>",
        )
        return

    if "selection" not in context.user_data:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please select a search term first. Hint: /switch",
        )
        return

    a = int(context.args[0])
    b = int(context.args[1])
    selected_search = context.user_data["selection"]
    with open(
        ROOT_DIR + "/data/" + selected_search.replace(" ", "_") + ".csv", "r"
    ) as f:
        df = pd.read_csv(f)
        df = df[(df["price"] >= a) & (df["price"] <= b)]
        for i in range(len(df)):
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=format_message(df.iloc[i]),
                parse_mode="Markdown",
            )


# add a new search to the list of monitored searches
def add(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Usage: /add <search term>",
        )
        return
    else:
        # check for comments
        # if context.args[0][0] == "[":
        #     comment = context.args[0][1:-1]
        #     context.args = context.args[1].strip()

        # check for min and max prices
        if "$" in context.args[-1] and "$" in context.args[-2]:
            # if the last two arguments are both prices, take them as a range of prices
            context_args = context.args[:-2]
            a = int(context.args[-2][1:])
            b = int(context.args[-1][1:])
            max_price = max(a, b)
            min_price = min(a, b)
        elif "$" in context.args[-1]:
            # if the last argument is a price, take it as the max_price
            context_args = context.args[:-1]
            max_price = int(context.args[-1][1:])
            min_price = None
        else:
            context_args = context.args
            max_price = None
            min_price = None

        # check for exclude keywords
        exclude = []
        for s in context_args:
            if "\\" in s:
                exclude.append(s[1:])
        for word in exclude:
            context_args.remove("\\" + word)
        new_search = " ".join(context_args)

        user_id = str(update.effective_user.id)

        # search and return error message if no results found
        # TODO: FIX THIS
        # if not scraper.search(new_search, exclude):
        #     context.bot.send_message(
        #         chat_id=update.effective_chat.id,
        #         text="Sorry, I couldn't find any listings for " + new_search,
        #     )
        #     return

        # valid results found, add to list of monitored searches
        if user_id in monitored_searches:
            monitored_searches[user_id]["searches"][new_search] = {
                "max_price": max_price,
                "min_price": min_price,
                "exclude": exclude,
            }
        else:
            monitored_searches[user_id] = {
                "searches": {
                    new_search: {
                        "max_price": max_price,
                        "min_price": min_price,
                        "exclude": exclude,
                    }
                }
            }

        context.user_data["selection"] = new_search

        output_str = (
            "Added new search term: '"
            + new_search
            + "' (max price: $"
            + str(max_price)
            + "; min price: $"
            + str(min_price)
            + ")"
        )
        if len(exclude) > 0:
            output_str += " (excluding: " + ", ".join(exclude) + ") "

        print(output_str + "to user_id: " + str(update.effective_chat.id))

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=output_str,
        )

        save_monitored_searches()


# switch from one monitored search to another
def switch(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in monitored_searches:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No monitored searches found. Use /add to add one.",
        )
        return
    keyboard = [
        [InlineKeyboardButton(x, callback_data="<switch> " + str(x))]
        for x in monitored_searches[user_id]["searches"]
    ]
    update.message.reply_text(
        "Please select one of the following searches: ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# set user selection based on button pressed
def switch_button(update: Update, context: CallbackContext):
    query = update.callback_query

    # every query must be answered, even if empty
    query.answer()

    # remove <switch> marker from data
    selection = " ".join(query.data.split()[1:])

    # save the selection to the user_data
    context.user_data["selection"] = selection

    query.edit_message_text(text=f"Selected option: {selection}")


# removes a search from monitored searches
def remove(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    if user_id not in monitored_searches:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No monitored searches found. Use /add to add one.",
        )
        return
    keyboard = [
        [InlineKeyboardButton(x, callback_data="<remove> " + str(x))]
        for x in monitored_searches[user_id]["searches"]
    ]
    update.message.reply_text(
        "Please select one of the following searches to remove: ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# removes the selected search from the list of monitored searches
def remove_button(update: Update, context: CallbackContext):
    query = update.callback_query

    # every query must be answered, even if empty
    query.answer()

    # remove <remove> marker from data
    selection = " ".join(query.data.split()[1:])

    monitored_searches[str(update.effective_chat.id)]["searches"].pop(selection, None)
    save_monitored_searches()
    os.remove(ROOT_DIR + "/data/" + selection.replace(" ", "_") + ".csv")

    query.edit_message_text(text=f"Search removed: {selection}")


# catch all
def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


# save monitored_searches
def save_monitored_searches():
    if not os.path.exists(os.path.join(ROOT_DIR, "data")):
        os.mkdir(os.path.join(ROOT_DIR, "data"))

    save_path = os.path.join(ROOT_DIR, "data", "monitored_searches.json")

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(monitored_searches, f, ensure_ascii=False, indent=4)


# checks if bot should send the update to the user
def should_send_update(row, user_id, search_term):
    if 'age' not in row:
        return False
    age = row["age"].split()

    # checks if the listing is new (< 1min old)
    is_recent = "second" in age[1]

    # checks if the listing is within the price range
    max_price = monitored_searches[user_id]["searches"][search_term]["max_price"]
    max_price = float("inf") if max_price is None else max_price
    min_price = monitored_searches[user_id]["searches"][search_term]["min_price"]
    min_price = 0 if min_price is None else min_price

    price = row['price']
    if math.isnan(price):
        return False
    is_within_price_range = min_price <= int(price) <= max_price

    # print(
    #    row["title"]
    #    + " is "
    #    + ("new" if is_recent else "old")
    #    + " and "
    #    + ("within" if is_within_price_range else "not within")
    # )

    return is_recent and is_within_price_range


# update all users on new listings
def push_to_all_users(updater):
    for user_id in monitored_searches:
        for search in monitored_searches[user_id]["searches"]:
            with open(
                ROOT_DIR + "/data/" + search.replace(" ", "_") + ".csv", "r"
            ) as f:
                df = pd.read_csv(f)
                m = df.apply(
                    lambda row: should_send_update(row, str(user_id), search), axis=1
                )
                listings_worth_seeing = df[m]
                print("listings_worth_seeing: ", listings_worth_seeing)
                for i in range(len(listings_worth_seeing)):
                    updater.bot.send_message(
                        chat_id=user_id,
                        text=format_message(listings_worth_seeing.iloc[i]),
                        parse_mode="Markdown",
                    )


# run when push_to_users script is run by crontab
def push_notification_checker(updater):
    listener = Listener(("localhost", 6000), authkey=b"password")
    running = True
    while running:
        try:
            conn = listener.accept()
            message = conn.recv()
            print(message)
            if message == "stop":
                running = False
                break
            else:
                push_to_all_users(updater)
            conn.close()
        except Exception as e:
            print(e)
            pass
    listener.close()


def main():
    with open(TOKEN_DIR, "r") as f:
        TOKEN = f.readline().strip()
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    recent_handler = CommandHandler("recent", recent)
    cheapest_handler = CommandHandler("cheapest", cheapest)
    price_range_handler = CommandHandler("range", price_range)
    add_handler = CommandHandler("add", add)
    switch_handler = CommandHandler("switch", switch)
    switch_button_hanlder = CallbackQueryHandler(switch_button, pattern="^<switch>")
    remove_handler = CommandHandler("remove", remove)
    remove_button_hanlder = CallbackQueryHandler(remove_button, pattern="^<remove>")
    unknown_handler = MessageHandler(Filters.command, unknown)

    all_handlers = [
        start_handler,
        recent_handler,
        cheapest_handler,
        price_range_handler,
        add_handler,
        switch_handler,
        switch_button_hanlder,
        remove_handler,
        remove_button_hanlder,
        unknown_handler,
    ]
    for handler in all_handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    push_notification_checker(updater)
    updater.idle()


if __name__ == "__main__":
    main()
