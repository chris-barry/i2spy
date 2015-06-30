# Client

## Dependencies

`pip install i2py`

* i2py - connecting to router information

The client expects that [i2pcontrol](http://itoopie.i2p) is installed.
Due to bugs, the head of the development branch is used right now.
This will change once a new version is pushed out.

## Running

Put this in a cronjob for once an hour at a random minute.

`http_proxy='http://127.0.0.1:4444'; python client.py --token $TOKEN`.

## Contributing

To become a data contributer you gotta know the right person.

To contribute code, put in a pull request or get me a diff via irc or email or whatever.

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
When it's set up a link will be posted here.

## License

[Unlicense](LICENSE).
