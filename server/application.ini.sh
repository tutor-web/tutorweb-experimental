###
# Generate application config from environment
###
OUTFILE=${1-/tmp/application.ini}

[ -n "${SERVER_CERT_PATH}" ] && SERVER_IS_HTTPS=true || SERVER_IS_HTTPS=false

cat <<EOF > ${OUTFILE}
# Generated by application.ini.sh - modifications will get overwritten

[app:main]
use = egg:tutorweb_quizdb

pyramid.reload_templates = false
pyramid.debug_authorization = false
pyramid.debug_notfound = false
pyramid.debug_routematch = false
pyramid.default_locale_name = en
pyramid.includes =
    pyramid_tm

sqlalchemy.url = ${DB_URL}
sqlalchemy.echo = false

tutorweb.material_bank.default = ${PROJECT_PATH}/db/material_bank

tutorweb.script.server_name = ${SERVER_NAME}
tutorweb.script.is_https = ${SERVER_IS_HTTPS}

tutorweb.lti.secrets = ${APP_LTI_SECRETS}

mail.default_sender = ${UWSGI_MAILSENDER}
mail.host = ${UWSGI_MAILHOST}
mail.port = ${UWSGI_MAILPORT}

EOF

# Fish out all smileycoin settings from the environment
set 2>&1 | grep -E '^APP_SMILEYCOIN_' | sed 's/APP_SMILEYCOIN_/smileycoin./g' | sed "s/'//g" >> ${OUTFILE}

cat <<EOF >> ${OUTFILE}

###
# wsgi server configuration
###

[server:main]
use = egg:waitress#main
unix_socket = ${UWSGI_SOCKET}
unix_socket_perms = 666
trusted_proxy = localhost
trusted_proxy_headers = x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port
EOF

cat <<EOF >> ${OUTFILE}

###
# logging configuration
# https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/logging.html
###

[loggers]
keys = root, tutorweb_quizdb

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = ${UWSGI_LOGLEVEL_ROOT}
handlers = console

[logger_tutorweb_quizdb]
level = ${UWSGI_LOGLEVEL_APP}
handlers =
qualname = tutorweb_quizdb

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s:%(lineno)s][%(threadName)s] %(message)s
EOF
