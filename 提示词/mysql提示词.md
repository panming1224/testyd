# MySQL 提示词集合

## 数据库连接
```sql
-- 连接到MySQL数据库
mysql -h localhost -u username -p database_name
```

## 基本查询
```sql
-- 查看所有数据库
SHOW DATABASES;

-- 使用特定数据库
USE database_name;

-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESCRIBE table_name;
```

## 数据操作
```sql
-- 插入数据
INSERT INTO table_name (column1, column2) VALUES (value1, value2);

-- 更新数据
UPDATE table_name SET column1 = value1 WHERE condition;

-- 删除数据
DELETE FROM table_name WHERE condition;

-- 查询数据
SELECT * FROM table_name WHERE condition;
```

## 表操作
```sql
-- 创建表
CREATE TABLE table_name (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

-- 修改表结构
ALTER TABLE table_name ADD COLUMN new_column VARCHAR(50);

-- 删除表
DROP TABLE table_name;
```

## 索引操作
```sql
-- 创建索引
CREATE INDEX index_name ON table_name (column_name);

-- 删除索引
DROP INDEX index_name ON table_name;
```

## 用户权限
```sql
-- 创建用户
CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';

-- 授权
GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```