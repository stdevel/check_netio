#!/bin/bash

# check_netio - check power states of Koukaan NETIO devices
#
# 2012 By Christian Stankowic
# <info at stankowic hyphen development dot net>
# https://github.com/stdevel
#

# Show help if wanted or invalid input
#$1	hostname
#$2	port
#$3	username
#$4	password
#$5	PORTS/TIME
if [ "$1" == "-h" ] || [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]; then
  echo "USAGE:	./check_netio.sh HOSTNAME PORT USERNAME PASSWORD MODE"
	echo ""
	echo "MODES:	time	check ntp synchronization"
	echo "		....	port states, e.g. 0000 for powered off"
	echo ""
	exit 0;
fi

if [ "$5" != "time" ]; then
	# Get port states
	PORTS=$(echo -e "login $3 $4\nport list\nquit"|nc -w 1 $1 $2|grep '[01][01][01][01]' | cut -d " " -f 2|tr -cd '\11\12\40-\176')

	if [ "$PORTS" == "$5" ]; then
		echo "OK: Port states matching"
		exit 0
	else
		echo "CRITICAL: Port states DON'T MATCH!"
		exit 2
	fi
else
	# Check time synchronization
	TIME=$(echo -e "login $3 $4\nsystem sntp\nquit" | nc -w 1 $1 $2 | tail -n2 | head -n1)
	if [[ "$TIME" == *"synchronized"* ]]; then
		# time synchronized
		echo "OK - time synchronized with SNTP server"
		exit 0
	else
		# time not synchronized
		echo "CRITICAL - time not synchronized with SNTP server"
		exit 2
	fi
fi
