CREATE DATABASE IF NOT EXISTS wego_db;
CREATE USER IF NOT EXISTS 'wegoride_user'@'%' IDENTIFIED BY 'wegoride';
GRANT ALL PRIVILEGES ON `wego_db`.* TO 'wegoride_user'@'%';
FLUSH PRIVILEGES;