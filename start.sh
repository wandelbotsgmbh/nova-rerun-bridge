#!/bin/sh

# Substitute environment variables in the NGINX config template
envsubst '${BASE_PATH}' < /app/nginx.http.conf.template > /etc/nginx/conf.d/default.conf

# Start NGINX
nginx &

# Start the Python processes
python -m rerun --serve-web --web-viewer-port 3000 --hide-welcome-screen --expect-data-soon &
python /app/nova_rerun_bridge/polling/populate.py &
python /app/nova_rerun_bridge/polling/stream_motion_groups.py &

# Wait for all background processes to finish
wait