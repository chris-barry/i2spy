#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# server.py - collect stats, share aggregrates.
# Author: Chris Barry <chris@barry.im>
# License: This is free and unencumbered software released into the public domain.
#
#
# TODO: Sexy charts: http://minimaxir.com/2015/02/ggplot-tutorial/
# TODO: More coherent error codes.
#
#
# Useful queries (there might be more efficient queries, send them in if you know them):
#   total unique routers seen
#     select count(*) from (select public_key,count(public_key) from netdb group by public_key);
#
#   routers with ipv6
#     select count(*) from (select public_key,count(public_key),ipv6 from netdb group by public_key) where ipv6=1;
#
#   count per country
#     select country,count(country) from (select country from netdb group by public_key) group by country;
#
#   count per signing key
#     select sign_key,count(sign_key) from (select sign_key from netdb group by public_key) group by sign_key;

import argparse, sqlite3, pprint, time
import i2pcontrol.pyjsonrpc

DATABASE='i2stat.db'
VERSION=1
conn=''
db=''

# Determine wheather or not a token is valid. 
def is_legit(token=''):
	conn = sqlite3.connect(DATABASE)
	cur = conn.cursor()
	#cur.execute('select * from nodes where token = ?;', token)
	results = cur.execute('select * from submitters where token=?', (token,)).fetchone()
	conn.commit()
	conn.close()
	return results

# Take data from a node.
def collect(token='', netdb='', local='', version=0):

	if not is_legit(token):
		raise i2pcontrol.pyjsonrpc.JsonRpcError(
			message = u'BAD_TOKEN',
			data = u'Your token is invalid. Go away or fix it.',
			code = -666
		)

	submission_time = time.time()
	conn = sqlite3.connect(DATABASE)
	cur = conn.cursor()
	inserts = []
	for router in netdb:
		'''
		# None of these checks are perfect, but they help to filter out bad data.
		if len(router['public_key']) >= 45:
			raise i2pcontrol.pyjsonrpc.JsonRpcError(
				message = u'BAD_DATA',
				data = u'Looks like the public key type submitted is bad.',
				code = -700
			)
		if len(router['sign_key']) >= 25:
			raise i2pcontrol.pyjsonrpc.JsonRpcError(
				message = u'BAD_DATA',
				data = u'Looks like the signing key type submitted is bad.',
				code = -701
			)
		if len(router['country']) != 2:
			raise i2pcontrol.pyjsonrpc.JsonRpcError(
				message = u'BAD_DATA',
				data = u'Looks like the country code submitted is bad.',
				code = -702
			)
		if len(router['ipv6']) != 1:
			raise i2pcontrol.pyjsonrpc.JsonRpcError(
				message = u'BAD_DATA',
				data = u'Looks like the ipv6 status submitted is bad.',
				code = -703
			)
		if not version.startswith('0.'):
			raise i2pcontrol.pyjsonrpc.JsonRpcError(
				message = u'BAD_DATA',
				data = u'Looks like the version submitted is bad.',
				code = -704
			)
		'''
		inserts.append((submission_time, router['public_key'], router['sign_key'], router['ipv6'], router['firewalled'], router['country'], router['version']))
	
	# TODO: i2pcontrol data is not being used yet.
	cur.executemany('insert into netdb (submitted, public_key, sign_key, ipv6, firewalled, country, version) values (?,?,?,?,?,?,?)', inserts)
	#cur.execute('insert into speeds (submitter, activepeers, hucapacitypeers, tunnelsparticipating, time) values (?,?,?,?,?)')

	conn.commit()
	conn.close()

	# This is done last because there should not be critical api changes too often.
	if version is not VERSION:
		raise i2pcontrol.pyjsonrpc.JsonRpcError(
			message = u'OLD',
			data = u'You\'re running an old version, please upgrade..',
			code = -6666
		)
	return 'good job'

# Jsonrpc class.
class DataSubmission(i2pcontrol.pyjsonrpc.HttpRequestHandler):
	methods = {
		'collect':collect
	}

# when you run this from a cli.
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-w', '--host', help='where to send data', type=str, default='localhost')
	parser.add_argument('-p', '--port', help='port of host', type=int,default=8080)
	parser.add_argument('-c', '--create', help='creates a new database (deletes old)', action='store_true')
	args = parser.parse_args()

	if args.create:
		print 'Making new database'
		con = sqlite3.connect(DATABASE)
		with open('schema.sql', mode='r') as f:
			con.cursor().executescript(f.read())
		con.commit()
		raise SystemExit, 0

	http_server = i2pcontrol.pyjsonrpc.ThreadingHttpServer(
		server_address = (args.host, args.port),
		RequestHandlerClass = DataSubmission
		)

	try:
		print 'Starting HTTP server ...'
		print ''.join(['URL: http://',args.host,':',str(args.port)])
		http_server.serve_forever()
	except KeyboardInterrupt:
		print 'Stopping HTTP server ...'
		http_server.shutdown()

