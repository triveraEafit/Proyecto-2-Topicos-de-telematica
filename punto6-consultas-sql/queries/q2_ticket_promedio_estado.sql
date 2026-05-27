-- Query 2: Ticket promedio por estado
SELECT 
    c.customer_state as estado,
    ROUND(AVG(op.payment_value), 2) as ticket_promedio,
    COUNT(DISTINCT o.order_id) as total_ordenes
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_payments op ON o.order_id = op.order_id
GROUP BY c.customer_state
ORDER BY ticket_promedio DESC
LIMIT 10;
