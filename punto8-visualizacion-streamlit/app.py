import os
import boto3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Olist Dashboard", layout="wide")

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOCAL_REFINED = Path(__file__).parent.parent / "punto7-pyspark" / "data" / "refined"

def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )

@st.cache_data(ttl=300)
def load(folder):
    if S3_BUCKET:
        path = f"s3://{S3_BUCKET}/refined/{folder}/"
        storage_options = {
            "key": os.getenv("AWS_ACCESS_KEY_ID"),
            "secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "token": os.getenv("AWS_SESSION_TOKEN"),
            "client_kwargs": {"region_name": AWS_REGION},
        }
        return pd.read_parquet(path, storage_options=storage_options)
    else:
        return pd.read_parquet(LOCAL_REFINED / folder)

def get_last_updated():
    if not S3_BUCKET:
        return "Local"
    try:
        s3 = get_s3_client()
        resp = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="refined/", MaxKeys=1)
        if resp.get("Contents"):
            ts = resp["Contents"][0]["LastModified"]
            return ts.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        pass
    return "N/A"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("ℹ️ Información")
    st.markdown("**Dataset:** Olist Brazilian E-Commerce")
    st.markdown("**Período:** 2016 – 2018")
    st.markdown("**Órdenes:** ~100k")
    st.markdown("**Tablas:** 9")
    st.markdown(f"**Fuente:** {'S3: ' + S3_BUCKET if S3_BUCKET else 'Local'}")
    st.markdown(f"**Actualizado:** {get_last_updated()}")
    st.markdown("---")
    st.markdown("[📁 GitHub](https://github.com/triveraEafit/Proyecto-2-Topicos-de-telematica)")
    st.markdown("ST0263 Tópicos de Telemática — EAFIT 2026-1")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📦 Olist E-Commerce — Dashboard de Análisis")
st.markdown("Análisis del dataset de Olist Brasil (2016-2018)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ticket por Estado",
    "😠 Reviews Negativas",
    "🚚 Entrega vs Score",
    "💰 Top Vendedores",
    "📅 Órdenes por Mes",
])

with tab1:
    st.subheader("Top 10 estados con mayor ticket promedio")
    df = load("q1_ticket_por_estado")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(df["customer_state"], df["avg_ticket"], color="steelblue")
    ax.set_xlabel("Ticket promedio (BRL)")
    ax.set_ylabel("Estado")
    ax.invert_yaxis()
    st.pyplot(fig)
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("Categorías con mayor tasa de reviews negativas")
    df = load("q2_reviews_negativas")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["category"], df["negative_rate_pct"], color="tomato")
    ax.set_xlabel("% reviews negativas")
    ax.invert_yaxis()
    st.pyplot(fig)
    st.dataframe(df, use_container_width=True)

with tab3:
    st.subheader("Correlación entre tiempo de entrega y satisfacción")
    df = load("q3_entrega_vs_score")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["delivery_bucket"], df["avg_review_score"], marker="o", color="green", linewidth=2)
    ax.set_xlabel("Días de entrega")
    ax.set_ylabel("Score promedio")
    ax.set_ylim(0, 5)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    st.dataframe(df, use_container_width=True)

with tab4:
    st.subheader("Top 20 vendedores por volumen de ventas")
    df = load("q4_top_vendedores")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(df["seller_id"].str[:12], df["total_revenue"], color="goldenrod")
    ax.set_xlabel("Revenue total (BRL)")
    ax.invert_yaxis()
    st.pyplot(fig)
    st.dataframe(df, use_container_width=True)

with tab5:
    st.subheader("Volumen de órdenes por mes y categoría")
    df = load("q5_ordenes_mes_categoria")
    top_cats = df.groupby("category")["total_orders"].sum().nlargest(5).index
    df_top = df[df["category"].isin(top_cats)]
    pivot = df_top.pivot_table(index="year_month", columns="category", values="total_orders", fill_value=0)
    fig, ax = plt.subplots(figsize=(14, 6))
    pivot.plot(ax=ax, linewidth=2)
    ax.set_xlabel("Mes")
    ax.set_ylabel("Órdenes")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    st.pyplot(fig)
    st.dataframe(df.head(50), use_container_width=True)

st.markdown("---")
st.caption("Proyecto 3 - ST0263 Topicos de Telematica | Datos: Olist Brazilian E-Commerce")
