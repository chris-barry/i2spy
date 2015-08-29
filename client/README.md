# Client

## Dependencies

`pip install i2py`

* i2py - connecting to router information
* I2PControl - for quering information from the router
	* Go to your [client config](http://127.0.0.1:7657/configclients) on your router and install i2p control with this url <http://plugins.i2p/files/I2PControl.xpi2p>.
	  It's needed near the bottom of the page.

## Running

Put this in a cronjob for once an hour at a random minute.

`http_proxy='http://127.0.0.1:4444'; python client.py --token $TOKEN`.

To generate a crontab entry, you can run:

`python client.py --cron`

## Contributing

To become a data contributer you gotta know the right person.

To contribute code, put in a pull request or get me a diff via irc, email, whatever crafty way you can think of.

## Privacy

I really don't want to take anything too personal.
Things that are will *never* be sent:

	* IP
	* Port
	* Uptime
	* Timezone
	* Sending router's public key

This list is subject to change, but will only change to reveal less information.

Everything collected will be presented publicly in raw and aggregate forms.
All data will be available under the creative commons zero license.

## License

[Unlicense](LICENSE).
