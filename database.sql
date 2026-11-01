CREATE DATABASE IF NOT EXISTS neuroprompt_db;
USE neuroprompt_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) DEFAULT '',
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prompt_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    language VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS analysis_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(100) NOT NULL,
    language VARCHAR(50) NOT NULL,
    code_input TEXT NOT NULL,
    detected_error TEXT NOT NULL,
    solution TEXT NOT NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

INSERT IGNORE INTO prompt_templates (username, title, language, code) VALUES
('System', 'Python API Request', 'Python', 'import requests\nres = requests.post("https://api.example.com", json={"key":"val"})\nprint(res.json())'),
('System', 'C++ Dynamic Array Allocator', 'C++', '#include <iostream>\nint* arr = new int[10];\n// process array');
