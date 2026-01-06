CREATE TABLE IF NOT EXISTS `wechat_bills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    `transaction_id` VARCHAR(64) NOT NULL UNIQUE COMMENT '交易单号',
    `transaction_time` DATETIME NOT NULL COMMENT '交易时间',
    `transaction_type` VARCHAR(50) COMMENT '交易类型',
    `direction` VARCHAR(20) COMMENT '收/支/其他',
    `payment_method` VARCHAR(50) COMMENT '交易方式',
    `amount` DECIMAL(12, 2) NOT NULL COMMENT '金额(元)',
    `counterparty` VARCHAR(255) COMMENT '交易对方',
    `merchant_id` VARCHAR(64) COMMENT '商户单号',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据导入时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;