#!/bin/bash
exec gunicorn -b :5000 --access-logfile - --error-logfile - people_counter:app