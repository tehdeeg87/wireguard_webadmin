FROM alpine:latest

# Install required packages
RUN apk add --no-cache curl jq bash

# Create the update script
COPY update_peer_hosts.sh /usr/local/bin/update_peer_hosts.sh
RUN chmod +x /usr/local/bin/update_peer_hosts.sh

# Create cron job to run every 5 minutes
RUN echo "*/5 * * * * /usr/local/bin/update_peer_hosts.sh" | crontab -

# Start cron in foreground
CMD ["crond", "-f"]