# Proyecto 3 - Big Data Pipeline en AWS
## ST0263 Tópicos Especiales en Telemática — EAFIT 2026-1

**Integrantes:**
- Tomas Gañan Rivera — tgananr@eafit.edu.co
- Pablo Baez Santamaria — pbaezs@eafit.edu.co

**Repositorio:** https://github.com/triveraEafit/Proyecto-2-Topicos-de-telematica

---

## Caso de Estudio
Brazilian E-Commerce (Olist) — análisis de un marketplace brasileño con ~100k órdenes, 9 tablas relacionales (orders, customers, products, sellers, reviews, payments, geolocation, order_items, order_payments).

**Dataset fuente:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

## Preguntas de Negocio
1. ¿Cuáles son los 10 estados con mayor ticket promedio de compra?
2. ¿Qué categorías de producto tienen mayor tasa de reviews negativas (score <= 2)?
3. ¿Cuál es la correlación entre tiempo de entrega y score de satisfacción del cliente?
4. ¿Cuáles son los vendedores con mayor volumen de ventas y mejor calificación promedio?
5. ¿En qué meses del año se concentra el mayor volumen de órdenes y cómo varía por categoría?

## Arquitectura

```
Fuentes → [RDS MariaDB | EC2 Files | URLs] → S3 raw/ → S3 trusted/ → S3 refined/
                                                  ↓              ↓
                                              AWS Glue       EMR/Hive
                                                                ↓
                                              Athena / SparkSQL / PySpark
                                                                ↓
                                                    Streamlit + Matplotlib
```

## Estructura del Repositorio
- `punto1-caso-estudio/` — Descripción del caso de estudio y dataset
- `punto2-fuentes-datos/` — Configuración de fuentes de datos (RDS, EC2, URLs)
- `punto3-ingesta/` — Scripts de ingesta hacia S3 raw
- `punto4-preparacion-glue/` — Jobs de AWS Glue para transformación (raw → trusted → refined)
- `punto5-catalogacion/` — Catalogación con AWS Glue Data Catalog
- `punto6-consultas-sql/` — Consultas con AWS Athena y SparkSQL
- `punto7-pyspark/` — Análisis con PySpark en EMR
- `punto8-visualizacion-streamlit/` — Dashboard con Streamlit y Matplotlib

## Tecnologías
AWS S3, AWS RDS (MariaDB), AWS Glue, AWS EMR (Spark + Hive), AWS Athena, AWS API Gateway, Python (PySpark, boto3, Streamlit, matplotlib), EC2
