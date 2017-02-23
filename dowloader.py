#!/usr/bin/python

#Python script to download files listed in queue.db using authentication
#Tested on Debian 9.0 (Stretch)

#apt install sqlite3
#need the following to install requests correctly, apt install python-requests isn't the same:
#apt install python-pip
#pip install requests

#use 'sed -i 's/\r//' downloader.py' to remove any spurious windows characters if editing via notepad++

#Set up SQLite db:
#sqlite3 queue.db
#CREATE TABLE sites (id INT NOT NULL PRIMARY KEY, name STRING NULL, username STRING NULL, password STRING NULL);
#CREATE TABLE queue2 (file STRING NOT NULL PRIMARY KEY, site INT NOT NULL, status STRING NULL, FOREIGN KEY(site) REFERENCES sites(id));

import sqlite3
import sys
import requests
import time

#Connection:
con = sqlite3.connect('queue.db')

#put all downloads in this folder:
path = '/path/to/download/location' #change this!

#By using 'with' keyword we get error handling, auto close connection and auto commit:
with con:
	cur = con.cursor()
	cur.execute('SELECT queue2.file, sites.username, sites.password FROM queue2 INNER JOIN sites ON queue2.site=sites.id')
	
	rows = cur.fetchall()
	
	print 'Downloading...'
	
	#print rows
	for row in rows:
		#print row[0], row[1], row[2] #to access each field separately
			
		url = row[0]
		#print 'URL=', url
		user = row[1]
		#print 'user=', user
		password = row[2]
		#print 'password=', password
		
		local_filename = url.split('/')[-1] #gets the filename from the last part of the url
		print 'file name=', local_filename
		
		r = requests.get(url, auth=(user, password))
		
		with open(path + local_filename, 'wb') as f:
			for chunk in r.iter_content(chunk_size=1024):
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
					#f.flush() #not sure what this really does or if it's necessary
		
		#Delete row if successful:
		if r.status_code == requests.codes.ok: #Requests comes with a built-in status code lookup object for easy reference
			print 'deleting db entry=', local_filename
			cur.execute('DELETE FROM queue2 WHERE file =?', (row[0],))
		
		#If not successful don't delete row and populate status column
		if r.status_code != requests.codes.ok:
			print 'failed to download =', local_filename
			cur.execute('UPDATE queue SET status=\'failed\' WHERE file=\'' + row[0] + "'")
		
print 'Finished at:', time.strftime("%X")
