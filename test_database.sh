#!/bin/bash
sudo docker rm -f mypostgres
sudo docker run --name mypostgres --net host -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres
sudo docker exec -it mypostgres psql -U postgres

CREATE DATABASE local_test_db;
CREATE USER test_user WITH PASSWORD 'mysecretpassword';
GRANT ALL PRIVILEGES ON DATABASE local_test_db TO test_user;
\q

sudo docker exec -it mypostgres psql -U postgres -d local_test_db
GRANT ALL ON SCHEMA public TO test_user;
\q

ngrok http --domain=exotic-crayfish-striking.ngrok-free.app 8000