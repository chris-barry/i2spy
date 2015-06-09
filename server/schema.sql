/* This is free and unencumbered software released into the public domain. */

/*
drop table if exists submitters;
create table submitters(
	id    integer primary key autoincrement,
	owner text not null,
	token text not null
);
*/

drop table if exists netdb;
create table netdb(
	id         integer primary key autoincrement,
	submitted  text    not null,
	public_key text    not null,
	sign_key   text    not null,
	ipv6       text    not null,
	firewalled text    not null,
	country    text    not null,
	version    text    not null
);

/* TODO: This table needs a lot of information added to it, but it's a start. */
drop table if exists speeds;
create table speeds(
	id                    integer primary key autoincrement,
	submitter             integer not null,
	activepeers           text    not null,
	hucapacitypeers       text    not null,
	tunnelsparticipating  text    not null,
	time                  text    not null
);
