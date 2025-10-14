FROM python:3.12-slim

RUN apt-get update && apt-get install -y wireguard-tools dnsmasq cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY haddns_multi.py /app/haddns_multi.py

# Set up cron job to run every minute
RUN echo "* * * * * /usr/bin/python3 /app/haddns_multi.py >> /var/log/haddns.log 2>&1" > /etc/cron.d/haddns \
    && chmod 0644 /etc/cron.d/haddns \
    && crontab /etc/cron.d/haddns

CMD ["cron", "-f"]