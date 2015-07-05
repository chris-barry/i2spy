#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# viewer.py - View aggregated i2p network statistics.
# Author: Chris Barry <chris@barry.im>
# License: This is free and unencumbered software released into the public domain.
#
# NOTE: This file should never write to the database, only read.

import argparse
import datetime
import math
import matplotlib
# We don't want matplotlib to use X11 (https://stackoverflow.com/a/3054314)
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sqlite3
import pandas as pd

from jinja2 import Environment, FileSystemLoader


interval = 3600    # = 60 minutes
num_intervals = 20 # = 10 hours
min_version = 20
min_country = 20
# http://i2p-projekt.i2p/en/docs/how/network-database#routerInfo
# H is left out since it's almost always empty.
#netdb_caps = ['f','H','K','L','M','N','O','P','R','U','X',]
netdb_caps = ['f','K','L','M','N','O','P','R','U','X',]

def query_db(conn, query, args=(), one=False):
	cur = conn.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

# TODO: Port to Pandas
def pie_graph(conn, query, output, title='', lower=0, log=False):
	labels = []
	sizes = []

	res = query_db(conn, query)
	# Sort so the graph doesn't look like complete shit.
	res = sorted(res, key=lambda tup: tup[1])
	for row in res:
		if row[1] > lower:
			labels.append(row[0])
			if log:
				sizes.append(math.log(row[1]))
			else:
				sizes.append(row[1])
	# Normalize.
	norm = [float(i)/sum(sizes) for i in sizes]

	plt.pie(norm,
			labels=labels,
			shadow=True,
			startangle=90,
	)
	plt.axis('equal')
	plt.legend()
	plt.title(title)
	plt.savefig(output)
	plt.close()

def plot_x_y(conn, query, output, title='', xlab='', ylab=''):
	df = pd.read_sql_query(query, conn)
	df['sh'] = pd.to_datetime(df['sh'], unit='s')
	df = df.set_index('sh')
	df.head(num_intervals).plot(marker='o')
	plt.title(title)
	plt.xlabel(xlab)
	plt.ylabel(ylab)
	plt.savefig(output)
	plt.close()

# Plots network traffic.
def i2pcontrol_stats(conn, output=''):
	things=[
		{'stat':'activepeers','xlab':'time','ylab':'total',},
		{'stat':'tunnelsparticipating','xlab':'time','ylab':'total',},
		{'stat':'decryptFail','xlab':'time','ylab':'total',},
		{'stat':'failedLookupRate','xlab':'time','ylab':'total',},
		{'stat':'streamtrend','xlab':'time','ylab':'total',},
		{'stat':'windowSizeAtCongestion','xlab':'time','ylab':'total',},
		#{'stat':'','xlab':'','ylab':'',}, # Template to add more.
		]

	tokens = query_db(conn, 'select owner,token from submitters;')
	for thing in things:
		combined=[]
		dfs=[]
		for token in tokens:
			q = 'select datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh, {1} from speeds where submitter="{2}" group by sh order by sh desc;'.format(interval, thing['stat'], token[1])
			df = pd.read_sql_query(q, conn)
			# unix -> human
			df['sh'] = pd.to_datetime(df['sh'], unit='s')
			dfs.append(df)

		# Reverse so it's put in left to right
		combined = reduce(lambda left,right: pd.merge(left,right,on='sh',how='outer'), dfs)
		combined.columns=['time'] + [i[0] for i in tokens]
		combined = combined.set_index('time')

		# Only 10 hours for now.
		combined.head(num_intervals).plot(marker='o')
		plt.title(thing['stat'])
		plt.xlabel(thing['xlab'])
		plt.ylabel(thing['ylab'])
		plt.savefig('{}/{}.png'.format(output, thing['stat']))
		plt.close()

# Make plot of how many nodes reported in.
def reporting_in(conn, output=''):
	q = 'select count(*) as count, datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh from speeds group by sh order by sh desc;'.format(interval)
	df = pd.read_sql_query(q, conn)
	# unix -> human
	df['sh'] = pd.to_datetime(df['sh'], unit='s')
	df = df.set_index('sh')
	''' TODO
	# We always want to see 0
	pylab.ylim(ymin=0)
	'''
	df.head(num_intervals).plot(marker='o')
	plt.title('reporting in')
	plt.xlabel('time')
	plt.ylabel('nodes')
	plt.savefig('{}/{}.png'.format(output, 'reporting-in'))
	plt.close()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--output-directory', help='where to save data',type=str, default='./output/')
	args = parser.parse_args()

	conn = sqlite3.connect('i2stat.db')

	# Activate pretty graphs.
	plt.style.use('ggplot')
	#plt.xkcd() # If you wanna be fun.

	# Graphs and stuff
	pie_graph(conn,
		query='select country,count(country) as count from (select country from netdb group by public_key) group by country;',
		output=args.output_directory+'country.png',
		title='Observed Countries',
		lower=min_country,
		log=False)
	pie_graph(conn,
		query='select version,count(version) as count from (select version from netdb group by public_key) group by version;',
		output=args.output_directory+'version.png',
		title='Observed versions',
		lower=min_version,
		log=False)
	pie_graph(conn,
		query='select sign_key,count(sign_key) as count from (select sign_key from netdb group by public_key) group by sign_key;',
		output=args.output_directory+'sign_key.png',
		title='Obverved Signing Keys',
		lower=0,
		log=True)

	for cap in netdb_caps:
		plot_x_y(conn,
			query='select count(caps), datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh from (select caps,public_key,submitted from netdb group by time(cast(((submitted)/({0})) as int)*{0}, "unixepoch"), public_key) where caps like "%{2}%" group by sh order by sh desc;'.format(interval, num_intervals, cap),
			output=args.output_directory+'{0}.png'.format(cap),
			title='Seen {0} Cap'.format(cap),
			xlab='Time',
			ylab='Total')

	plot_x_y(conn,
		query='select count(ipv6), datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh from (select ipv6,public_key,submitted from netdb group by time(cast(((submitted)/({0})) as int)*{0}, "unixepoch"), public_key) where ipv6=1 group by sh order by sh desc;'.format(interval, num_intervals),
		output=args.output_directory+'ipv6.png',
		title='Seen IPv6',
		xlab='Time',
		ylab='Total')
	plot_x_y(conn,
		query='select count(firewalled), datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh from (select firewalled,public_key,submitted from netdb group by time(cast(((submitted)/({0})) as int)*{0}, "unixepoch"), public_key) where firewalled=1 group by sh order by sh desc;'.format(interval, num_intervals),
		output=args.output_directory+'firewalled.png',
		title='Seen firewalled',
		xlab='Time',
		ylab='Total')

	plot_x_y(conn,
		query='select count(firewalled), datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh from (select firewalled,public_key,submitted from netdb group by time(cast(((submitted)/({0})) as int)*{0}, "unixepoch"), public_key) group by sh order by sh desc;'.format(interval, num_intervals),
		output=args.output_directory+'submitted.png',
		title='Unique Submitted Per Submission',
		xlab='Time',
		ylab='Total')

	reporting_in(conn, output=args.output_directory)
	i2pcontrol_stats(conn, output=args.output_directory)

	# Numbers and stuff.
	total = query_db(conn, 'select count(*) from (select public_key,count(public_key) from netdb group by public_key);')
	ipv6_total = query_db(conn, 'select count(*) from (select public_key,count(public_key),ipv6 from netdb group by public_key) where ipv6=1;')
	fw_total = query_db(conn, 'select count(*) from (select public_key,count(public_key),firewalled from netdb group by public_key) where firewalled=1;')
	versions = query_db(conn, 'select version,count(version) as count from (select version from netdb group by public_key) group by version having count > {} order by count desc;'.format(min_version))
	countries = query_db(conn, 'select country,count(country) as count from (select country from netdb where firewalled=0 group by public_key) group by country having count >= {} order by count(country) desc;'.format(min_country))
	sign_keys = query_db(conn, 'select sign_key,count(sign_key) as count from (select sign_key from netdb group by public_key) group by sign_key order by count(sign_key) desc;')
	sightings = query_db(conn, 'select version, datetime(min(submitted), "unixepoch") from netdb group by version order by submitted;')

	# The selects should be averages per period. This is a bit messy but should be right.
	speeds = query_db(conn, 'select submitter,avg(activepeers),avg(tunnelsparticipating), datetime(cast(((submitted)/({0})) as int)*{0}, "unixepoch") as sh , \
	count(*) as count from speeds group by sh limit {1};'.format(interval, num_intervals))

	env = Environment(loader=FileSystemLoader('templates'))
	template = env.get_template('index.html')
	output = template.render(
		total=total[0][0],
		ipv6_total=ipv6_total[0][0],
		fw_total=fw_total[0][0],
		sightings=sightings,
		versions=versions,
		countries=countries,
		sign_keys=sign_keys,
		speeds=speeds,
		netdb_caps=netdb_caps,
		time=str(datetime.datetime.utcnow())[:-3]
	)
	with open(args.output_directory+'index.html', 'wb') as f:
		f.write(output)

