#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# client.py - i2p clients share what they know to a centralized server.
# Author: Chris Barry <chris@barry.im>
# License: This is free and unencumbered software released into the public domain.

import argparse
import i2pcontrol
import netdb
import i2pcontrol.pyjsonrpc

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
	parser.add_argument('-s', '--server', help='where to send data',type=str, default='tuuql5avhexhn7oq4lhyfythxejgk4qpavxvtniu3u3hwfwkogmq.b32.i2p')
	parser.add_argument('-p', '--port', help='where to send data',type=int, default='80')
	parser.add_argument('-t', '--token', help='token to prove yourself',type=str, default='')
	args = parser.parse_args()

	if not args.token:
		print 'Use a token. See --help for usage.'
		raise SystemExit, 0

	rpc = i2pcontrol.pyjsonrpc.HttpClient(
		url = ''.join(['http://',args.server,':',str(args.port)]),
		gzipped = True
	)
	
	# NetDB Stuff
	netdb.inspect(hook=print_entry)

	# Local router stuff
	a = i2pcontrol.I2PController()
	vals = a.getRouterInfo()
	this_router = {
		'activepeers'          : vals['i2p.router.netdb.activepeers'],
		'fastpeers'            : vals['i2p.router.netdb.fastpeers'],
		'highcapacitypeers'    : vals['i2p.router.netdb.highcapacitypeers'],
		'tunnelsparticipating' : vals['i2p.router.net.tunnels.participating'],
	}

	try:
		rpc.collect(token=args.token, netdb=routers, local=this_router, version=VERSION)
	except i2pcontrol.pyjsonrpc.JsonRpcError, err:
		print 'Error code {}: {} -- {}'.format(err.code, err.message, err.data)
		

