-- Query 5: Métodos de pago más usados
SELECT 
    payment_type as metodo_pago,
    COUNT(order_id) as total_transacciones,
    ROUND(AVG(payment_value), 2) as valor_promedio,
    ROUND(SUM(payment_value), 2) as valor_total
FROM order_payments
GROUP BY payment_type
ORDER BY total_transacciones DESC;
