#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# client.py - i2p clients share what they know to a centralized server.
# Author: Chris Barry <chris@barry.im>
# License: This is free and unencumbered software released into the public domain.

import argparse
import i2py.netdb
import i2py.control
import i2py.control.pyjsonrpc

routers = []
VERSION = 1

# Aggregreates a buncha data
def print_entry(ent):
	n = ent.dict()
	country = '??'
	ipv6 = False
	firewalled = False

	for a in n['addrs']:
		if a.location and a.location.country:
			country = a.location.country
			ipv6 = 1 if ':' in a.location.ip else 0
			firewalled = 1 if a.firewalled else 0
			break
	
	routers.append({
		'public_key' : n['pubkey'],
		'sign_key'   : n['cert']['signature_type'],
		'crypto_key' : n['cert']['crypto_type'],
		'version'    : n['options']['coreVersion'],
		'country'    : country,
		'ipv6'       : ipv6,
		'firewalled' : firewalled,
		})
	
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='prints request json instead of sending',type=bool, default=False)
	parser.add_argument('-i', '--i2p-directory', help='I2P home',type=str, default='~/.i2p/')
	parser.add_argument('-s', '--server', help='where to send data',type=str, default='tuuql5avhexhn7oq4lhyfythxejgk4qpavxvtniu3u3hwfwkogmq.b32.i2p')
	parser.add_argument('-p', '--port', help='where to send data',type=int, default='80')
	parser.add_argument('-t', '--token', help='token to prove yourself',type=str, default='')
	args = parser.parse_args()

	if not args.token:
		print 'Use a token. See --help for usage.'
		raise SystemExit, 1

	rpc = i2py.control.pyjsonrpc.HttpClient(
		url = ''.join(['http://',args.server,':',str(args.port)]),
		gzipped = True
	)

	# Local router stuff
	try:
		a = i2py.control.I2PController()
	except:
		print 'I2PControl not installed, or router is down.'
		raise SystemExit, 1

	ri_vals = a.get_router_info()
	
	this_router = {
		'activepeers'          : ri_vals['i2p.router.netdb.activepeers'],
		'fastpeers'            : ri_vals['i2p.router.netdb.fastpeers'],
		'highcapacitypeers'    : ri_vals['i2p.router.netdb.highcapacitypeers'],
		'tunnelsparticipating' : ri_vals['i2p.router.net.tunnels.participating'],
		'netDb.writePending'   : a.get_rate(stat='netDb.writePending', period=3600), # TODO: Send more info
	}
	
	# NetDB Stuff
	i2py.netdb.inspect(hook=print_entry,netdb_dir=args.i2p_directory)

	try:
		if args.debug:
			# To check the approximate size of a request, run this. No network call is sent. Results in bytes.
			# $ python client.py | gzip --stdout | wc --bytes
			print i2py.control.pyjsonrpc.create_request_json("collect", token=args.token, netdb=routers, local=this_router, version=VERSION)
		else:
			rpc.collect(token=args.token, netdb=routers, local=this_router, version=VERSION)
	except i2py.control.pyjsonrpc.JsonRpcError, err:
		print 'Error code {}: {} -- {}'.format(err.code, err.message, err.data)
		
