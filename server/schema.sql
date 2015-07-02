/* This is free and unencumbered software released into the public domain. */

drop table if exists submitters;
create table submitters(
	id    integer primary key autoincrement,
	owner text unique not null,
	token text unique not null
);

drop table if exists netdb;
create table netdb(
	id         integer primary key autoincrement,
	submitted  date    not null,

	ipv6       boolean not null,
	firewalled boolean not null,
	public_key text    not null,
	sign_key   text    not null,
	country    text    not null,
	caps       text    not null,
	version    text    not null
);

/* TODO: This table needs a lot of information added to it, but it's a start. */
drop table if exists speeds;
create table speeds(
	id                    integer primary key autoincrement,
	submitter             integer not null,
	submitted             date    not null,

	activepeers           integer not null,
	tunnelsparticipating  integer not null,
	decryptFail           float   not null,
	failedLookupRate      float   not null,
	streamtrend           float   not null,
	windowSizeAtCongestion float   not null
);

