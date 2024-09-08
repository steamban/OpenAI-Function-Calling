# Use the official PostgreSQL v16 image as the base
FROM postgres:16

# Install the vector extension dependencies and build it
RUN apt-get update && \
    apt-get install -y git build-essential postgresql-server-dev-16 && \
    git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector && \
    apt-get remove -y git build-essential && \
    apt-get autoremove -y && \
    apt-get clean

# Set the environment variables for PostgreSQL
ENV POSTGRES_USER=admin \
    POSTGRES_PASSWORD=admin \
    POSTGRES_DB=ezza_docs

# Create a directory to persist the data
VOLUME /var/lib/postgresql/data

# Copy the initialization script into the container
COPY init_db.sh /docker-entrypoint-initdb.d/

# Expose the default PostgreSQL port
EXPOSE 5432

# Run the PostgreSQL server
CMD ["postgres"]
