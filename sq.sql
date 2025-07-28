-- 创建名为 crypto_alert 的数据库，如果不存在则创建
CREATE DATABASE IF NOT EXISTS crypto;
-- 使用 crypto_alert 数据库
USE crypto;


-- 在 crypto_alert 数据库中创建 twitter_entries 表，如果不存在则创建
CREATE TABLE IF NOT EXISTS twitter_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link VARCHAR(512) NOT NULL,
    description TEXT,
    published DATETIME,
    tweet_id VARCHAR(255) NOT NULL UNIQUE,
    author VARCHAR(255), -- 添加作者字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);