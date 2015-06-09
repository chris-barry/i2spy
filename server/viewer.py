#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# flask.py - Boilerplate for simple Flask project.
# Author: Chris Barry <chris@barry.im>
# License: This is free and unencumbered software released into the public domain.
#
# NOTE: This file should never write to the database, only read.

import os
import base64
from flask import Flask, render_template, g, redirect, request, make_response
from sqlite3 import dbapi2 as sqlite3

app = Flask(__name__)
app.debug = True

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'i2stat.db'),
	DEBUG=True,
	SECRET_KEY='development key',
	USERNAME='admin',
	PASSWORD='default'
))

## ----------
## DB Stuff
## Via: http://flask.pocoo.org/docs/0.10/patterns/sqlite3/
## ----------

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

def get_db():
	if not hasattr(g, 'flask.sql3'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

def connect_db():
	rv = sqlite3.connect(app.config['DATABASE'])
	rv.row_factory = sqlite3.Row
	return rv

def query_db(query, args=(), one=False):
	cur = get_db().execute(query, args)
	rv = cur.fetchall()
	cur.close()
	return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

## -------------- ##
## Static Routes  ##
## -------------- ##

@app.route('/')
@app.route('/index.html')
def index():
	total = query_db('select count(*) from (select public_key,count(public_key) from netdb group by public_key);')
	ipv6_total = query_db('select count(*) from (select public_key,count(public_key),ipv6 from netdb group by public_key) where ipv6=1;')
	fw_total = query_db('select count(*) from (select public_key,count(public_key),firewalled from netdb group by public_key) where firewalled=1;')
	versions = query_db('select version,count(version) as count  from (select version from netdb group by public_key) group by version order by count desc;')
	countries = query_db('select country,count(country) as count from (select country from netdb group by public_key) group by country order by count(country) desc;')
	sign_keys = query_db('select sign_key,count(sign_key) as count from (select sign_key from netdb group by public_key) group by sign_key order by count(sign_key) desc;')
	return render_template('index.html', total=total[0][0], ipv6_total=ipv6_total[0][0], fw_total=fw_total[0][0], versions=versions, countries=countries, sign_keys=sign_keys)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', error=error), 404

# Checking for POST Request.
#if request.method == 'POST':

'''
## -------------- ##
## Dynamic Route  ##
## -------------- ##

@app.route('/url/<param>')
def url(param=None):
	return render_template('url.html', param=param)
'''

if __name__ == '__main__':
	#app.run()
	app.run(host='0.0.0.0', port=7373)


