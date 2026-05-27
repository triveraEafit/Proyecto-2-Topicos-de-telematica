-- Query 1: Top 10 categorías de productos más vendidas
SELECT 
    ct.product_category_name_english as categoria,
    COUNT(oi.order_id) as total_ventas
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
GROUP BY ct.product_category_name_english
ORDER BY total_ventas DESC
LIMIT 10;
