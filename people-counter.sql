create database people_counter;
SET FOREIGN_KEY_CHECKS = 0;
use people_counter;
drop table if exists `user`;
CREATE TABLE IF not exists `role`(
	`id` int(2) NOT NULL auto_increment primary key,
    `role_name` varchar(20) NOT NULL
);

CREATE TABLE IF NOT exists `user`(
	`id` int(11) NOT NULL auto_increment,
    `name` varchar(30) NOT NULL,
    `password` varchar(30) NOT NULL,
    `status` int(2) NOT NULL,
    `role_id` int(2) NOT NULL,
    PRIMARY KEY(`id`),
    foreign key fk_role_user(`role_id`) references `role`(`id`)
)engine = InnoDB default charset=utf8 comment='user_table';
alter table user change `password` `password` varchar(200);
alter table user add last_message_read_time datetime default null;

CREATE TABLE IF NOT EXISTS `video`(
	`id` int(11) NOT NULL PRIMARY KEY auto_increment,
    `location` VARCHAR(200) NOT NULL
);
alter table video add `name` varchar(200);

drop table if exists `history`;
CREATE TABLE IF NOT EXISTS `history`(
	`id` int(11) NOT NULL auto_increment primary key,
    `user_id` int(11) NOT NULL,
    `count` int(11) NOT NULL,
    `video_id` int(11) NOT NULL,
    `submit_time` datetime default NULL,
    `status` int(2) NOT NULL,
    foreign key fk_history_user(`user_id`) references `user`(`id`),
    foreign key fk_history_video(`video_id`) references `video`(`id`)
);

drop table if exists `message`;
CREATE TABLE IF NOT EXISTS `message`(
	`id` int(11) NOT NULL auto_increment primary key,
    `user_id` int(11) NOT NULL,
    `content` varchar(200) NOT NULL,
    `time_stamp` datetime default NULL,
    foreign key fk_message_user(`user_id`) references `user`(`id`)
);

INSERT INTO `role` values('1', 'user');
INSERT INTO `role` values('2', 'manager');