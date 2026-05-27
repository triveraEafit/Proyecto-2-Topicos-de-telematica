-- Query 4: Tiempo promedio de entrega por estado
SELECT 
    c.customer_state as estado,
    ROUND(AVG(date_diff('day',
        date_parse(CAST(o.order_purchase_timestamp AS varchar), '%Y-%m-%d %H:%i:%s.%f'),
        date_parse(CAST(o.order_delivered_customer_date AS varchar), '%Y-%m-%d %H:%i:%s.%f')
    )), 1) as dias_promedio_entrega,
    COUNT(o.order_id) as total_ordenes
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_delivered_customer_date IS NOT NULL
AND o.order_purchase_timestamp IS NOT NULL
GROUP BY c.customer_state
ORDER BY dias_promedio_entrega DESC
LIMIT 10;
