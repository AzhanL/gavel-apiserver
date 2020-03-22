#!/bin/bash
# Must already have executed 'pipenv shell' and be in the python virtual environment
cd ..

echo "Pulling updates..."
git pull

./manage.py makemigrations
./manage.py migrate

echo "Please enter root password to kill old processes..."
su - root -c "pkill -f uwsgi -9"

uwsgi --yaml uwsgi.yaml &
disown