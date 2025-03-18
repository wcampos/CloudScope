FROM postgres:16-alpine

# Install necessary tools
RUN apk add --no-cache bash

# Copy migration scripts and wait-for-db script
COPY *.sql /docker-entrypoint-initdb.d/
COPY wait-for-db.sh /usr/local/bin/wait-for-db.sh

# Make scripts executable
RUN chmod +x /docker-entrypoint-initdb.d/*.sql \
    && chmod +x /usr/local/bin/wait-for-db.sh

# Create backups directory
RUN mkdir -p /backups && chmod 755 /backups

ENTRYPOINT ["/usr/local/bin/wait-for-db.sh", "db"] 