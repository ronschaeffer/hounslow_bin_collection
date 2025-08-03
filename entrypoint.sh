#!/bin/sh
# entrypoint.sh
echo "${CRON_SCHEDULE:-50 2 * * *} python /app/waste_sync.py >> /proc/1/fd/1 2>>/proc/1/fd/2" > /etc/cron.d/waste-sync-cron
chmod 0644 /etc/cron.d/waste-sync-cron
crontab /etc/cron.d/waste-sync-cron
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
