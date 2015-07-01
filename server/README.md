# The Server Bits

Collection and viewing are in two parts:

## Dependencies

`pip install jinja2 i2py matplotlib`

* jinja2 - template engnine
* i2py - connecting to router information
* matplotlib - plots

## Collection

```
python collector.py --add --username a --token b # Add a user.
python collector.py -c                           # Create the DB
python collector.py                              # Listen for submissions
```

## Generating Report

```
# Make sure you have some data in the database, and the directory is made.
python viewer.py -o out-dir/
```

