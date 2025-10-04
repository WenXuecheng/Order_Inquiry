-- Demo orders for testing (12 rows)
-- Usage:
--   mysql -h <host> -u <user> -p automatica < db/seed_demo_orders.sql
-- wooden_crate: 1=打木架，0=不打，NULL=未填写

USE `automatica`;

INSERT INTO orders (order_no, group_code, weight_kg, wooden_crate, shipping_fee, status)
VALUES
  -- A2025 group
  ('CN2025001', 'A2025', 2.45, 0,    NULL,   '打包发出'),
  ('CN2025002', 'A2025', 1.10, 1,    12.80,  '在我国海岸等待检查'),
  ('CN2025003', 'A2025', 3.88, NULL, 28.50,  '已发往俄罗斯'),

  -- B2025 group
  ('CN2025004', 'B2025', 4.60, 1,    52.00,  '等待俄罗斯关口检查'),
  ('CN2025005', 'B2025', 0.92, 0,    NULL,   '转运到彼得堡（1-3天）'),
  ('CN2025006', 'B2025', 2.14, NULL, 32.40,  '已到达彼得堡'),

  -- Unclassified (code "A" 查询未分类)
  ('CN2025007', NULL,    1.77, NULL, NULL,   '打包发出'),
  ('CN2025008', '',      6.05, 0,    82.00,  '已发往俄罗斯'),

  -- C2025 group
  ('CN2025009', 'C2025', 2.95, NULL, NULL,   '已结算'),
  ('CN2025010', 'C2025', 3.33, 0,    46.00,  '等待俄罗斯关口检查'),

  -- VIP001 group（示例特殊客户）
  ('CN2025011', 'VIP001', 4.20, 1,   88.00,  '已结算'),
  ('CN2025012', 'VIP001', 5.50, NULL, NULL,  '已到达彼得堡')
;
