#!/bin/bash

# Get Docker0 IP
DOCKER_IP=$(ip addr show docker0 | grep -Po 'inet \K[\d.]+')

# Stop and remove existing container if it exists
sudo docker stop mypostgres 2>/dev/null
sudo docker rm mypostgres 2>/dev/null

# Run new Docker container
sudo docker run --name mypostgres --net host -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres

# Wait for PostgreSQL to start
sleep 5

# Create database and user
sudo docker exec -it mypostgres psql -U postgres -c "CREATE DATABASE local_test_db;"
sudo docker exec -it mypostgres psql -U postgres -c "CREATE USER test_user WITH PASSWORD 'mysecretpassword';"
sudo docker exec -it mypostgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE local_test_db TO test_user;"

# Grant schema privileges
sudo docker exec -it mypostgres psql -U postgres -d local_test_db -c "GRANT ALL ON SCHEMA public TO test_user;"

# Output database URL
echo "Database URL: postgresql://test_user:mysecretpassword@$DOCKER_IP:5432/local_test_db"