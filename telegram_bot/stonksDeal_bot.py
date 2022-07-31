from tkinter import W
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

from scraper import scraper

DEFAULT_COLS = ["title", "price", "age"]
CAROUSELL_URL = "https://www.carousell.sg"

if os.path.exists("./data/monitored_searches.txt"):
    with open("./data/monitored_searches.txt", "r") as index_file:
        monitored_searches = index_file.readlines()
        monitored_searches = [x.strip() for x in monitored_searches]
        print("\nLoaded monitered searches: " + str(monitored_searches) + "\n")
else:
    print("\nNo monitored searches file found, creating new one\n")
    monitored_searches = []

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
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
    with open("./data/" + selected_search.replace(" ", "_") + ".csv", "r") as f:
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
    with open("./data/" + selected_search.replace(" ", "_") + ".csv", "r") as f:
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
    with open("./data/" + selected_search.replace(" ", "_") + ".csv", "r") as f:
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
        new_search = " ".join(context.args)
        monitored_searches.append(new_search)
        scraper.new_search(new_search)
        context.user_data["selection"] = new_search
        print("\nAdded new search: " + new_search + "\n")
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Added search term: " + new_search,
        )


# switch from one monitored search to another
def switch(update: Update, context: CallbackContext):
    if len(monitored_searches) == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No monitored searches found. Use /add to add one.",
        )
        return
    keyboard = [[InlineKeyboardButton(x, callback_data=x)] for x in monitored_searches]
    update.message.reply_text(
        "Please select one of the following searches: ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# set user selection based on button pressed
def switch_button(update: Update, context: CallbackContext):
    query = update.callback_query

    # every query must be answered, even if empty
    query.answer()

    # save the selection to the user_data
    context.user_data["selection"] = query.data

    query.edit_message_text(text=f"Selected option: {query.data}")


# catch all
def unknown(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main():
    with open("./config.txt", "r") as f:
        TOKEN = f.readline().strip()
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler("start", start)
    recent_handler = CommandHandler("recent", recent)
    cheapest_handler = CommandHandler("cheapest", cheapest)
    price_range_handler = CommandHandler("range", price_range)
    add_handler = CommandHandler("add", add)
    switch_handler = CommandHandler("switch", switch)
    switch_button_hanlder = CallbackQueryHandler(switch_button)
    unknown_handler = MessageHandler(Filters.command, unknown)

    all_handlers = [
        start_handler,
        recent_handler,
        cheapest_handler,
        price_range_handler,
        add_handler,
        switch_handler,
        switch_button_hanlder,
        unknown_handler,
    ]
    for handler in all_handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()
    updater.idle()

    with open("./data/monitored_searches.txt", "w") as index_file:
        for search in monitored_searches:
            index_file.write(search + "\n")
        print("\nSaved monitored searches: " + str(monitored_searches) + "\n")


if __name__ == "__main__":
    main()
