#!/bin/bash
python manage.py migrate                  # Apply database migrations
python manage.py collectstatic --noinput  # Collect static files

# Prepare log files and start outputting logs to stdout
touch ${PROJECT_SRVHOME}/logs/gunicorn.log
touch ${PROJECT_SRVHOME}/logs/access.log
tail -n 0 -f ${PROJECT_SRVHOME}/logs/*.log &

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn ${PROJECT_NAME}.wsgi:application \
    --name ${PROJECT_NAME} \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --log-file=${PROJECT_SRVHOME}/logs/gunicorn.log \
    --access-logfile=${PROJECT_SRVHOME}/logs/access.log \
    "$@"
