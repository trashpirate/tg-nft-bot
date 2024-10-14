#!/bin/bash

# Stop and remove any existing 'mypostgres' container
sudo docker rm -f mypostgres

# Run a new PostgreSQL container with the specified name and configuration
sudo docker run --name mypostgres --net host -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to initialize..."
sleep 5

# Create the database and user with appropriate privileges
sudo docker exec -i mypostgres psql -U postgres <<EOF
CREATE DATABASE local_test_db;
CREATE USER test_user WITH PASSWORD 'mysecretpassword';
GRANT ALL PRIVILEGES ON DATABASE local_test_db TO test_user;
EOF

# Grant all privileges on the public schema to the user
sudo docker exec -i mypostgres psql -U postgres -d local_test_db <<EOF
GRANT ALL ON SCHEMA public TO test_user;
EOF

echo "PostgreSQL setup complete!"

# sudo docker rm -f mypostgres
# sudo docker run --name mypostgres --net host -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres
# sudo docker exec -it mypostgres psql -U postgres

# CREATE DATABASE local_test_db;
# CREATE USER test_user WITH PASSWORD 'mysecretpassword';
# GRANT ALL PRIVILEGES ON DATABASE local_test_db TO test_user;
# \q

# sudo docker exec -it mypostgres psql -U postgres -d local_test_db
# GRANT ALL ON SCHEMA public TO test_user;
# \q

# ngrok http --domain=exotic-crayfish-striking.ngrok-free.app 8000