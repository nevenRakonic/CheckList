drop table if exists posts;
drop table if exists users;
drop table if exists lists;
drop table if exists permissions;

create table users (
  id integer primary key autoincrement,
  username varchar(30) not null,
  password text not null,
  join_date date not null
);

create table lists (
  id integer primary key autoincrement,
  name text not null,
  created date not null,
  author_id references users(id),
  author references users(username)
);

create table permissions (
  user_id references users(id),
  list_id references lists(id),
  primary key(user_id, list_id)

);

create table posts (
  id integer primary key autoincrement,
  list_id text not null,
  body text not null,
  status text not null CHECK (status IN ('DONE','WIP','TODO')),
  post_time date not null,
  author references users(username),
  foreign key(list_id) references lists(id)
);

