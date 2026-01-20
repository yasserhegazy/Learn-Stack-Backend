-- MySQL initialization script
-- This script runs when the database container is first created

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges
GRANT ALL PRIVILEGES ON lms_db.* TO 'lms_user'@'%';
FLUSH PRIVILEGES;

-- Show databases
SHOW DATABASES;
