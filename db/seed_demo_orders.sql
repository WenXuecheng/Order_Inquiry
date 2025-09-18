-- Demo orders for testing (10 rows)
-- Usage:
--   mysql -h <host> -u <user> -p automatica < db/seed_demo_orders.sql

USE `automatica`;

INSERT INTO orders (order_no, group_code, weight_kg, shipping_fee, status)
VALUES
  -- A666 group
  ('CN1001', 'A666', 2.30, NULL, '打包发出'),
  ('CN1002', 'A666', 1.00, 12.00, '在我国海岸等待检查'),
  ('CN1003', 'A666', 3.50, NULL, '已发往俄罗斯'),

  -- B777 group
  ('CN1004', 'B777', 4.20, 50.00, '等待俄罗斯关口检查'),
  ('CN1005', 'B777', 0.80, NULL, '转运到彼得堡（1-3天）'),
  ('CN1006', 'B777', 2.00, 30.00, '已到达彼得堡'),

  -- Unclassified (A means query unclassified)
  ('CN1007', NULL,   1.70, NULL, '打包发出'),
  ('CN1008', '',     5.10, 70.00, '已发往俄罗斯'),

  -- C888 group
  ('CN1009', 'C888', 2.60, NULL, '已结算'),
  ('CN1010', 'C888', 3.20, 40.00, '等待俄罗斯关口检查')
;

