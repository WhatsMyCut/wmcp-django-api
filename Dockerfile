FROM python:3.5.5-jessie

ENV APP_DIR /opt/app
ENV APP_LOGS /tmp/wmcp/logs/
ENV PYTHONUNBUFFERED 1
ENV SSH_MODE false
ENV DJANGO_SETTINGS_MODULE whatsmycut.settings.local
ENV SESSION_COOKIE_PATH "/"

WORKDIR ${APP_DIR}
COPY . ./
COPY ./scripts/wait-for-it.sh ./scripts/start.sh /

RUN chmod +x /wait-for-it.sh /start.sh \
  && mkdir -p ${APP_LOGS} \
  && pip3 install --upgrade pip \
  && pip3 install dumb-init \
  && pip3 install -r requirements.txt

EXPOSE 8000 3001 22

# Runs "dumb-init -- <CMD>"
ENTRYPOINT ["dumb-init", "--", "/wait-for-it.sh", "db:5432", "--"]

CMD ["bash", "-c", "/start.sh", "bash"]
