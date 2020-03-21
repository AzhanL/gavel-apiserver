#!/bin/bash
cd ..

pipenv shell

su - root -c "pkill -f uwsgi -9"

git pull

./manage.py makemigrations
./manage.py migrate

uwsgi --yaml uwsgi.yaml