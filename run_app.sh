#!/usr/bin/env bash

gunicorn todos.app:application --workers 4 -b 127.0.0.1:5000
