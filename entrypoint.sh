#!/bin/sh
# Hounslow Bin Collection container entrypoint
#
# If CRON_SCHEDULE is set, sets up cron and runs the command on schedule.
# If CALENDAR_ENABLED is true, starts an HTTP server for ICS files.
# Otherwise, runs the command once and exits.

set -e

# Copy default config on first run
if [ ! -f /app/config/config.yaml ]; then
    if [ -f /app/config-defaults/config.yaml.example ]; then
        cp /app/config-defaults/config.yaml.example /app/config/config.yaml
        echo "Copied default config.yaml to /app/config/"
    fi
fi

# Start calendar web server in background if enabled
if [ "${CALENDAR_ENABLED:-true}" = "true" ]; then
    echo "Starting calendar web server on port ${ICS_PORT:-8080}..."
    hounslow-bins serve --port "${ICS_PORT:-8080}" &
fi

# If CRON_SCHEDULE is set, run as a scheduled service
if [ -n "$CRON_SCHEDULE" ]; then
    echo "Setting up cron schedule: $CRON_SCHEDULE"

    # Build the cron command — run the entrypoint args on schedule
    COMMAND="$*"
    echo "$CRON_SCHEDULE cd /app && $COMMAND >> /proc/1/fd/1 2>>/proc/1/fd/2" > /etc/cron.d/hounslow-bins
    chmod 0644 /etc/cron.d/hounslow-bins
    crontab /etc/cron.d/hounslow-bins

    # Run once immediately on start, then hand off to cron
    echo "Running initial collection..."
    $COMMAND || true

    echo "Starting cron daemon..."
    exec cron -f
else
    # One-shot mode: run the command and exit
    exec "$@"
fi
