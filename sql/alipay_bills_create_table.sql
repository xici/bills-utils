CREATE TABLE IF NOT EXISTS `alipay_bills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `transaction_time` DATETIME NOT NULL COMMENT '交易时间',
    `category` VARCHAR(50) COMMENT '交易分类',
    `counterparty` VARCHAR(255) COMMENT '交易对方',
    `counterparty_account` VARCHAR(255) COMMENT '对方账号',
    `product_name` VARCHAR(255) COMMENT '商品说明',
    `direction` VARCHAR(20) COMMENT '收/支',
    `amount` DECIMAL(12, 2) NOT NULL COMMENT '金额',
    `payment_method` VARCHAR(100) COMMENT '收/付款方式',
    `status` VARCHAR(50) COMMENT '交易状态',
    `transaction_id` VARCHAR(64) NOT NULL UNIQUE COMMENT '交易订单号',
    `merchant_id` VARCHAR(64) COMMENT '商家订单号',
    `remark` TEXT COMMENT '备注',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;