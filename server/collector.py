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
import i2py.control.pyjsonrpc

DATABASE='i2stat.db'
VERSION=1
conn=''
db=''

# Figure out if we should even allow a submission.
def is_legit(conn, token='', version=0):
	cur = conn.cursor()

	results = cur.execute('select * from submitters where token=?', (token,)).fetchone()
	recent = cur.execute('select submitted from speeds where submitter=? order by submitted desc limit 1;',[token]).fetchone()

	if not results:
		conn.close()
		print 'Received invalid submission due to bad token.'
		raise i2py.control.pyjsonrpc.JsonRpcError(
			message = u'BAD_TOKEN',
			data = u'Your token is invalid. Go away or fix it.',
			code = -666
		)

	# Give it 80 minutes to account for some time error.
	# None means it's new.
	if recent is not None and (time.time() - float(recent[0])) < 80*60:
		conn.close()
		raise i2py.control.pyjsonrpc.JsonRpcError(
			message = u'SLOW_DOWN',
			data = u'You are submitting too often.',
			code = -6667
		)

	if version is not VERSION:
		conn.close()
		raise i2py.control.pyjsonrpc.JsonRpcError(
			message = u'OLD',
			data = u'You\'re running an old version, please upgrade..',
			code = -6668
		)
	print 'Got from {}'.format(results)
	return True

# Take data from a node.
def collect(token='', netdb='', local='', asn={}, version=0):
	conn = sqlite3.connect(DATABASE)

	is_legit(conn, token, version)

	submission_time = time.time()
	cur = conn.cursor()
	r_inserts = []
	a_inserts = []

	for asn,count in asn.iteritems():
		a_inserts.append((submission_time,asn,count))
		
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
		r_inserts.append((submission_time, router['public_key'], router['sign_key'], router['ipv6'], router['firewalled'], router['country'], router['version'], router['caps']))
	
	cur.executemany('insert into netdb (submitted, public_key, sign_key, ipv6, firewalled, country, version, caps) values (?,?,?,?,?,?,?,?)', r_inserts)
	cur.executemany('insert into asn (submitted, asn, count) values (?,?,?)', a_inserts)
	cur.execute('insert into speeds (submitter, activepeers, tunnelsparticipating, submitted, decryptFail, failedLookupRate, streamtrend, windowSizeAtCongestion) values (?,?,?,?,?,?,?,?)', [token,local['activepeers'],local['tunnelsparticipating'],submission_time, local['decryptFail'],local['failedLookupRate'],local['streamtrend'],local['windowSizeAtCongestion']])

	conn.commit()
	conn.close()

	return 'good job'

# Jsonrpc class.
class DataSubmission(i2py.control.pyjsonrpc.HttpRequestHandler):
	methods = {
		'collect':collect
	}

# when you run this from a cli.
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--add', help='add new user', action='store_true')
	parser.add_argument('-c', '--create', help='creates a new database (deletes old)', action='store_true')
	parser.add_argument('-d', '--delete', help='remove a user', action='store_true')
	parser.add_argument('-p', '--port',  help='port of host', type=int,default=8080)
	parser.add_argument('-t', '--token', help='token for submitter', type=str, default=None)
	parser.add_argument('-u', '--user', help='name for submitter', type=str, default=None)
	parser.add_argument('-w', '--host', help='where to send data', type=str, default='localhost')
	args = parser.parse_args()

	if args.create:
		print 'Making new database'
		con = sqlite3.connect(DATABASE)
		with open('schema.sql', mode='r') as f:
			con.cursor().executescript(f.read())
		con.commit()
		con.close()
		raise SystemExit, 0
	
	if args.delete:
		con = sqlite3.connect(DATABASE)
		user = args.user
		token = args.token
		if user is None:
			print 'Enter a --user.'
			raise SystemExit, 0
		con.execute('delete from submitters where owner=?;', [user])
		con.commit()
		con.close()
		raise SystemExit, 0
		
	if args.add:
		con = sqlite3.connect(DATABASE)
		user = args.user
		token = args.token
		if user is None or token is None:
			print 'Enter a --user and a --token.'
			raise SystemExit, 0
		con.execute('insert into submitters (owner,token) values (?,?);', [user,token])
		con.commit()
		con.close()
		raise SystemExit, 0
		

	http_server = i2py.control.pyjsonrpc.ThreadingHttpServer(
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

