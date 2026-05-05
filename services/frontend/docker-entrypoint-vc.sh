#!/bin/sh
set -e
# URL pública del API tal como la ve el navegador (runtime). Genera /config.json antes de nginx.
URL="${VC_API_BASE_URL:-http://localhost:8000}"
URL="${URL%/}"
escaped=$(printf '%s' "$URL" | awk '{gsub(/\\/,"\\\\"); gsub(/"/,"\\\""); print}')
printf '{"apiBaseUrl":"%s"}\n' "$escaped" > /usr/share/nginx/html/config.json
exec /docker-entrypoint.sh "$@"
