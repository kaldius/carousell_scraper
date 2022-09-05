#!/usr/bin/env bash

read -p "Delete token? (y/n) " answer
if [ "$answer" == "y" ]; then
    rm ./config/token.txt
    echo "Token deleted."
fi

read -p "Delete data? (y/n) " answer
if [ "$answer" == "y" ]; then
    rm -rf ./data
    echo "Data deleted."
fi

read -p "Delete python virtual environment?" answer
if [ "$answer" == "y" ]; then
    rm -r scraper_venv
    echo "Python virtual environment deleted."
fi

rm cron_scrape.sh
rm start_bot.sh
echo "Cron scripts deleted."

crontab -l | grep -v "cron_scrape.sh" | crontab -
crontab -l | grep -v "start_bot.sh" | crontab -
echo "Cron jobs deleted."
