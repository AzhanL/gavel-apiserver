#!/bin/bash
# Must already have executed 'pipenv shell' and be in the python virtual environment
cd ..

pipenv shell

echo "Pulling updates..."
git pull

./manage.py makemigrations
./manage.py migrate

echo "Please enter root password to kill old processes..."
su - root -c "pkill -f uwsgi -9"
sleep 3

uwsgi --yaml uwsgi.yaml &
disown