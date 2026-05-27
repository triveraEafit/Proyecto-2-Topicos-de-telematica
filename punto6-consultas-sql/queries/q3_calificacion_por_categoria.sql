-- Query 3: Calificación promedio por categoría
SELECT 
    ct.product_category_name_english as categoria,
    ROUND(AVG(CAST(r.review_score AS double)), 2) as calificacion_promedio,
    COUNT(r.review_id) as total_reviews
FROM order_reviews r
JOIN orders o ON r.order_id = o.order_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
JOIN category_translation ct ON p.product_category_name = ct.product_category_name
GROUP BY ct.product_category_name_english
ORDER BY calificacion_promedio DESC
LIMIT 10;
