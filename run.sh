#!/bin/bash

cd "$(dirname "$0")"
echo `pwd`
while :
do
	echo "Starting FileServer Service"
	 .env/bin/python SimpleFileServer.py

	sleep 5
done

