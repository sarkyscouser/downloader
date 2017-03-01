#!/usr/bin/python

#Python script to download files in queue.db using usernames and passwords

#need the following to install 3rd party libraries:
#apt install python-pip
#pip install requests
#pip install progressbar

#use 'sed -i 's/\r//' filename' to remove any spurious windows characters if editing via notepad++

##########Set up SQLite db:#########
#sqlite3 queue.db
#CREATE TABLE sites (id INT NOT NULL PRIMARY KEY, name STRING NULL, username STRING NULL, password STRING NULL);
#CREATE TABLE queue2 (file STRING NOT NULL PRIMARY KEY, site INT NOT NULL, status STRING NULL, FOREIGN KEY(site) REFERENCES sites(id));
#.exit
####################################

import sqlite3
import sys
import requests
import time
import progressbar

#Connection:
con = sqlite3.connect('queue.db')

#put all downloads in this folder:
path = '/path/to/download/folder/'

#By using 'with' keyword we get error handling, auto close connection and auto commit:
with con:
	cur = con.cursor()
	cur.execute('SELECT queue2.file, sites.username, sites.password FROM queue2 INNER JOIN sites ON queue2.site=sites.id')
	
	rows = cur.fetchall()
	
	print 'Downloading...'
	
	#print rows
	for row in rows:
		url = row[0]
		#print 'URL=', url
		user = row[1]
		#print 'user=', user
		password = row[2]
		#print 'password=', password
		
		local_filename = url.split('/')[-1] #gets the filename from the last part of the url
		print 'file name=', local_filename
		
		r = requests.get(url, auth=(user, password), stream=True)
		
		if r.status_code == requests.codes.ok: #Requests comes with a built-in status code lookup object for easy reference
		
			file_size = int(r.headers['content-length'])
			print 'file size (int)=', file_size
		
			chunk = 1024
			num_bars = int(file_size / chunk)
			bar = progressbar.ProgressBar(maxval=num_bars).start()
			i = 0
		
			with open(path + local_filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=chunk):
					if chunk: # filter out keep-alive new chunks
						f.write(chunk)
						bar.update(i)
						i += 1
						#f.flush() #not sure if this is necessary
		
			#Delete row if successful:
			print '\n' #to put a line between progress bar and next lines
			print 'deleting db entry=', local_filename
			cur.execute('DELETE FROM queue2 WHERE file =?', (row[0],))
		
		else:
			#If requests fails, don't delete db row and populate status column
			if r.status_code != requests.codes.ok:
				print 'failed to download =', local_filename
				#cur.execute('UPDATE queue SET status=\'failed\' WHERE file=\'' + row[0] + "'")
				cur.execute('UPDATE queue SET status=' + str(r.status_code) + ' WHERE file=\'' + row[0] + "'")
		
print 'Finished at:', time.strftime("%X")
