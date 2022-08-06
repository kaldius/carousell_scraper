#!/usr/bin/env bash

read -p "Delete token? (y/n) " answer
if [ "$answer" == "y" ]; then
    rm ./config/token.txt
fi

rm -r scraper_venv
rm cron_scrape.sh
rm start_bot.sh

crontab -l | grep -v "cron_scrape.sh" | crontab -
crontab -l | grep -v "start_bot.sh" | crontab -