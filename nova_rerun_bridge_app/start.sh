#!/bin/sh

# Substitute environment variables in the NGINX config template
envsubst '${BASE_PATH}' < /app/nginx.http.conf.template > /etc/nginx/conf.d/default.conf

# Start NGINX
nginx &

# Start the Python processes
python /app/populate.py &

# Wait for all background processes to finish
wait