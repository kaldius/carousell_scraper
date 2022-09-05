#!/usr/bin/env bash

# save token
read -p "Please key in your telegram bot token: " token
echo "$token" > ./config/token.txt

# install python dependencies
echo "Creating python virtual environment and installing dependencies..."
python -m venv scraper_venv
source scraper_venv/bin/activate
pip install -r requirements.txt

# create cron scripts
echo "Creating cron scripts..."
echo "source $PWD/scraper_venv/bin/activate && python $PWD/scrape_once.py && sleep 5s && python $PWD/push_to_users.py" > cron_scrape.sh
echo "source $PWD/scraper_venv/bin/activate && python $PWD/main.py" > start_bot.sh

read -p "Do you want to set the recommended cron jobs? (y/n) " answer
if [ "$answer" == "y" ]; then
    echo "Setting cron jobs..."
    # write out current crontab
    crontab -l > mycron
    # echo new cron into cron file
    echo "* * * * * bash $PWD/cron_scrape.sh >> $PWD/scraper_logs.log 2>&1" >> mycron
    echo "@reboot bash $PWD/start_bot.sh >> $PWD/bot_logs.log 2>&1" >> mycron
    # install new cron file
    crontab mycron
    rm mycron

    read -p "A reboot is required before the cron jobs can be started. Reboot now? (y/n) " answer
    if [ "$answer" == "y" ]; then
        reboot
    fi
fi
