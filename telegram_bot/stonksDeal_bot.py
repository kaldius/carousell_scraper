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
from config.definitions import ROOT_DIR, CAROUSELL_URL, TOKEN_DIR
import csv

from scraper import scraper

load_path = os.path.join(ROOT_DIR, "data", "monitored_searches.csv")

if os.path.exists(load_path):
    with open(load_path, "r") as f:
        reader = csv.reader(f)
        monitored_searches = {int(row[0]): row[1:] for row in reader}
        print(monitored_searches)
else:
    print("No monitored searches file found, creating new one.")
    monitored_searches = {}

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
        new_search = " ".join(context.args)

        user_id = update.effective_user.id

        if user_id in monitored_searches:
            monitored_searches[user_id].append(new_search)
        else:
            monitored_searches[user_id] = [new_search]
        scraper.search(new_search)

        context.user_data["selection"] = new_search

        print(
            "\nAdded new search '"
            + new_search
            + "' to user_id: "
            + str(update.effective_chat.id)
        )

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Added search term: " + new_search,
        )

        save_monitored_searches()


# switch from one monitored search to another
def switch(update: Update, context: CallbackContext):
    user_id = update.effective_chat.id
    if user_id not in monitored_searches:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No monitored searches found. Use /add to add one.",
        )
        return
    keyboard = [
        [InlineKeyboardButton(x, callback_data=x)] for x in monitored_searches[user_id]
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

    # save the selection to the user_data
    context.user_data["selection"] = query.data

    query.edit_message_text(text=f"Selected option: {query.data}")


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

    with open("./data/monitored_searches.csv", "w") as f:
        writer = csv.writer(f)
        keys = monitored_searches.keys()
        for key in keys:
            writer.writerow([key] + monitored_searches[key])


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


if __name__ == "__main__":
    main()
