-- Automatica MySQL schema (idempotent)
-- Safe to run multiple times

-- Optional: enforce UTF-8 and UTC
-- SET NAMES utf8mb4;
-- SET time_zone = '+00:00';

CREATE DATABASE IF NOT EXISTS `automatica`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `automatica`;

CREATE TABLE IF NOT EXISTS `orders` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `order_no` VARCHAR(64) NOT NULL,
  `group_code` VARCHAR(64) NULL,
  `weight_kg` DOUBLE NULL,
  `shipping_fee` DOUBLE NULL,
  `status` VARCHAR(64) NOT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_order_no` (`order_no`),
  KEY `idx_group_code` (`group_code`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Optional demo data (uncomment to test)
-- INSERT INTO orders (order_no, group_code, weight_kg, status, shipping_fee)
-- VALUES
-- ('CN0001', '2025-01', 2.5, '打包发出', NULL),
-- ('CN0002', '2025-01', 1.2, '已发往俄罗斯', 30),
-- ('CN0003', NULL,       3.0, '等待俄罗斯关口检查', NULL);

