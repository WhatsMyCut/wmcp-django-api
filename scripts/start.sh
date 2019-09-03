#!/usr/bin/env bash

cd /opt/app

echo "SSH_MODE MODE ${AMENIFY_SSH}"

if [[ "$SSH_MODE" == "1" || "$SSH_MODE" == "true" ]]; then
  /usr/sbin/sshd -D
else
  python ./manage.py makemigrations && python ./manage.py migrate && python ./manage.py runserver 0:8000
fi
