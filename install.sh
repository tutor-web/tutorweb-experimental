#!/bin/sh
set -ex

# This script will create a systemd unit for running the backend, and
# an nginx config.
#
# It is tested on Debian, but should hopefully work on anything systemd-based.

[ -e ".local-conf" ] && . ./.local-conf

# ---------------------------
# Config options, to override any of these, set them in .local.conf

PROJECT_PATH="${PROJECT_PATH-$(dirname "$(readlink -f "$0")")}"
SERVICE_MODE="${SERVICE_MODE-development}"
SERVER_NAME="${SERVER_NAME-$(hostname --fqdn)}"
SERVER_CERT_PATH="${SERVER_CERT_PATH-}"  # e.g. /etc/nginx/ssl/certs
SERVICE_NAME="${SERVICE_NAME-tutorweb}"
SERVICE_FILE="${SERVICE_FILE-/etc/systemd/system/${SERVICE_NAME}.service}"
UWSGI_BIN="${UWSGI_BIN-${PROJECT_PATH}/server/bin/uwsgi}"
UWSGI_USER="${UWSGI_USER-nobody}"
UWSGI_GROUP="${UWSGI_GROUP-nogroup}"
UWSGI_SOCKET="${UWSGI_SOCKET-/tmp/${SERVICE_NAME}_uwsgi.${SERVICE_MODE}.sock}"
UWSGI_TIMEOUT="${UWSGI_TIMEOUT-5m}"
UWSGI_PROCESSES="${UWSGI_PROCESSES-4}"
UWSGI_THREADS="${UWSGI_THREADS-4}"
UWSGI_API_CACHE_TIME="${UWSGI_API_CACHE_TIME-60m}"
UWSGI_CACHE_SIZE="${UWSGI_CACHE_SIZE-1g}"
[ "${SERVICE_MODE}" = "production" ] && UWSGI_CACHE_ZONE="${UWSGI_CACHE_ZONE-api_cache}" || UWSGI_CACHE_ZONE="${UWSGI_CACHE_ZONE-off}"

set | grep -E 'UWSGI|SERVICE'

# ---------------------------
# Systemd unit file to run uWSGI

systemctl | grep -q "${SERVICE_NAME}.service" && systemctl stop ${SERVICE_NAME}.service
cat <<EOF > ${SERVICE_FILE}
[Unit]
Description=uWSGI daemon for ${SERVICE_NAME}
After=network.target

[Service]
ExecStart=${UWSGI_BIN} \
    --master \
    --processes=${UWSGI_PROCESSES} --threads=${UWSGI_THREADS} \
    --enable-threads --thunder-lock \
    --mount /=tutorweb_quizdb.web:app \
    --chmod-socket=666 \
    -s ${UWSGI_SOCKET}
WorkingDirectory=${PROJECT_PATH}/server
User=${UWSGI_USER}
Group=${UWSGI_GROUP}
Restart=on-failure
RestartSec=5s
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
EOF

if [ "${SERVICE_MODE}" = "production" ]; then
    [ -f "${UWSGI_SOCKET}" ] && chown ${UWSGI_USER}:${UWSGI_GROUP} "${UWSGI_SOCKET}"
    systemctl enable ${SERVICE_NAME}.service
    systemctl start ${SERVICE_NAME}.service
else
    systemctl disable ${SERVICE_NAME}.service
    systemctl stop ${SERVICE_NAME}.service
fi

# ---------------------------
# NGINX config for serving clientside
echo -n "" > /etc/nginx/sites-available/${SERVICE_NAME}

if [ -n "${SERVER_CERT_PATH}" ]; then
    cat <<EOF >> /etc/nginx/sites-available/${SERVICE_NAME}
server {
    listen      80;
    server_name ${SERVER_NAME};

    location /.well-known/acme-challenge/ {
        alias "${SERVER_CERT_PATH}/acme-challenge/";
    }

    return 301 https://\$server_name\$request_uri;
}

server {
    listen [::]:443 ssl;
    listen      443 ssl;
    server_name ${SERVER_NAME};

    ssl_certificate      ${SERVER_CERT_PATH}/certs/${SERVER_NAME}/fullchain.pem;
    ssl_certificate_key  ${SERVER_CERT_PATH}/certs/${SERVER_NAME}/privkey.pem;
    ssl_trusted_certificate ${SERVER_CERT_PATH}/certs/${SERVER_NAME}/fullchain.pem;
    ssl_dhparam ${SERVER_CERT_PATH}/dhparam.pem;

    # https://mozilla.github.io/server-side-tls/ssl-config-generator/
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    # intermediate configuration. tweak to your needs.
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:ECDHE-RSA-DES-CBC3-SHA:ECDHE-ECDSA-DES-CBC3-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA';
    ssl_prefer_server_ciphers on;

EOF
else
    cat <<EOF >> /etc/nginx/sites-available/${SERVICE_NAME}
server {
    listen      80;
    server_name ${SERVER_NAME};
EOF
fi

cat <<EOF >> /etc/nginx/sites-available/${SERVICE_NAME}
    charset     utf-8;
    root "${PROJECT_PATH}/client/www";
    gzip        on;

    proxy_intercept_errors on;
    error_page 502 503 504 /error/bad_gateway.json;

    location /api/ {
        proxy_pass  http://unix:${UWSGI_SOCKET}:/api/;
        proxy_set_header Host            \$host;
        proxy_set_header X-Forwarded-For \$remote_addr;
    }

    location /mathjax/ {
        alias "${PROJECT_PATH}/client/node_modules/mathjax/";
    }

    location / {
        try_files \$uri \$uri.html /index.html;
    }
}
EOF
ln -fs /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
nginx -t
systemctl reload nginx.service
