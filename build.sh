#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_slots
python manage.py collectstatic --no-input
