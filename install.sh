#!/usr/bin/env bash

# save token
read -p "Please key in your telegram bot token: " token
echo "$token" > ./config/token.txt

# install python dependencies
python -m venv scraper_venv
source scraper_venv/bin/activate
pip install -r requirements.txt

# create cron script
echo "source $PWD/scraper_venv/bin/activate && python $PWD/scrape_once.py" > cron_scrape.sh
echo "source $PWD/scraper_venv/bin/activate && python $PWD/main.py" > start_bot.sh

# write out current crontab
crontab -l > mycron
# echo new cron into cron file
echo "0,10,20,30,40,50 * * * * bash $PWD/cron_scrape.sh >> $PWD/scraper_logs.log 2>&1" >> mycron
echo "@reboot bash $PWD/start_bot.sh >> $PWD/bot_logs.log 2>&1" >> mycron
# install new cron file
crontab mycron
rm mycron

read -p "carousell_scraper requires a reboot to complete installation. Reboot now? (y/n) " answer
if [ "$answer" == "y" ]; then
    reboot
fi