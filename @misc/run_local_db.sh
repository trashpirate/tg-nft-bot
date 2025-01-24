#!/bin/bash

# Define variables
POSTGRES_CONTAINER_NAME="mypostgres"
POSTGRES_USER="test_user"
POSTGRES_PASSWORD="mysecretpassword"
POSTGRES_DB="local_test_db"
POSTGRES_PORT=5432

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo "Error: Docker is not installed. Please install Docker first." >&2
  exit 1
fi

# Check if the container is already running
if [ "$(docker ps -q -f name=$POSTGRES_CONTAINER_NAME)" ]; then
  docker rm -f $POSTGRES_CONTAINER_NAME
  echo "Deleting running '$POSTGRES_CONTAINER_NAME'. "
fi

# Check if the container already exists
if [ "$(docker ps -aq -f name=$POSTGRES_CONTAINER_NAME)" ]; then
  echo "A container with the name '$POSTGRES_CONTAINER_NAME' already exists. Starting it now..."
  docker start $POSTGRES_CONTAINER_NAME
else
  # Run PostgreSQL container
  echo "Starting a new PostgreSQL container..."
  docker run -d \
    --name $POSTGRES_CONTAINER_NAME \
    -e POSTGRES_USER=$POSTGRES_USER \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e POSTGRES_DB=$POSTGRES_DB \
    -p $POSTGRES_PORT:5432 \
    postgres
fi

# Print success message
echo "PostgreSQL is running."
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  Username: $POSTGRES_USER"
echo "  Password: $POSTGRES_PASSWORD"
