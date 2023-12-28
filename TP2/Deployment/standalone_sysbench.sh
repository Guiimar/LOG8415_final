#!/bin/bash

#install requirements
sudo apt-get -y update
sudo apt-get install mysql-server -y
sudo apt install sysbench -y
sudo apt install wget

#Download sakila database on the instance
sudo apt-get install unzip
sudo mkdir sakila
cd sakila
sudo wget https://downloads.mysql.com/docs/sakila-db.zip
sudo unzip sakila-db.zip

#sudo mysql_secure_installation
# update the password
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password'"

#install the database
sudo mysql -u root --password=password -e "SOURCE /home/ubuntu/sakila/sakila-db/sakila-schema.sql"
sudo mysql -u root --password=password -e "SOURCE /home/ubuntu/sakila/sakila-db/sakila-data.sql" 

sudo mysql -u root --password=password -e "USE sakila" 

#Launch the benchmark
sudo sysbench oltp_read_write --table-size=100000 --mysql-db=sakila --mysql-user=root --mysql-password=password prepare
sudo sysbench oltp_read_write --table-size=100000 --threads=6 --max-time=60 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=password  run > /home/ubuntu/results.txt
sudo sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --mysql-password=password cleanup
