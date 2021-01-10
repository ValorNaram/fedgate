#!/usr/bin/bash
# Requirements:
#	- Linux like environment
#	- psql
#	- bash
#	- executing this script on the same localhost as the database lives.
#	- running this script as the database superuser ('postgres' usually).
	
# This file needs to be executed on the same (virtual) machine/environment as the database is because otherwise this script will not work as you want it to do
# This is a good limitation because creating databases is a critical thing this should be only carried out by sysadmins.


# begin area 1
echo "checking, if the current user is a database superuser..."
permission=$(psql -t -A -c "SELECT usesuper FROM pg_user WHERE usename='$USER'")
if [ "$permission"="t" ]; then
	echo -e "	- \e[0;32mUser '$USER' has the necessary permission to create a database and to set the owner \e[0;m"
else
	echo -e "	- \e[0;31mUser '$USER' lacks the necessary permission to create a database and to set the owner \e[0;m"
	echo "		- closing script..."
	exit "100" # The current user is not a database superuser
fi

# end area 1
# begin area 2
true=0
dbname=""
databases=$(psql -t -A -c "SELECT datname FROM pg_database") # get all databases stored in postgresql
while [ $true -eq 0 ];
do
	echo "Please type in the name of the database you want to create:"
	read dbname
	if [ -n $(echo $databases | grep "$dbname") ];
	then
		echo -e "	- \e[0;32mDatabase '$dbname' doesn't exist which is great :) \e[0;m"
		true=1
	else
		echo -e "	- \e[0;31mDatabase '$dbname' does exist already which is bad :( \e[0;m"
		echo "		- asking again..."
	fi
done

# end area 2
# begin area 3
true=0
user=""
users=$(psql -t -A -c "SELECT usename FROM pg_user")
while [ $true -eq 0 ];
do
	echo "Please type in the name of the owner user for database '$dbname':"
	read user
	if [ -n $(echo $users | grep "$user") ];
	then
		echo -e "	- \e[0;31mDatabase user '$user' doesn't exist which is bad :(\e[0;m"
		echo "		- asking again..."
	else
		echo -e "	- \e[0;32mDatabase '$dbname' does exist which is good :)[0;m"
		true=1
	fi
done

# end area 3
# begin area 4
echo "Attempting to create database '$dbname' with user '$user' as its owner..."
psql -c "CREATE DATABASE $dbname WITH OWNER '$user';"
if [ $? -eq 0 ]
then
	echo -e "	\e[0;32mSuccess!\e[0;m"
else
	echo -e "	\e[0;31mFailure!\e[0;m"
	exit $?
fi
# end area 4
