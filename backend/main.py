"""
backend/main.py
===============
API REST para el dashboard de Global Superstore.
Endpoints analíticos con filtros dinámicos.
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from typing import Optional
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "dbname":   os.getenv("DB_NAME",     "superstore"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Global Superstore Analytics API",
    description="API analítica sobre el dataset Global Superstore de Kaggle. Proyecto de portafolio.",
    version="1.0.0",
    contact={"name": "Portfolio Project"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kemetian96.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── DB HELPER ─────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def query(sql: str, params=None):
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def query_one(sql: str, params=None):
    result = query(sql, params)
    return result[0] if result else {}

# ── FILTRO HELPER ─────────────────────────────────────────────────────────────
def build_where(year=None, category=None, region=None, segment=None, market=None):
    """Construye cláusula WHERE dinámica según los filtros activos."""
    conditions = []
    params     = []

    if year:
        conditions.append("EXTRACT(YEAR FROM order_date) = %s")
        params.append(int(year))
    if category:
        conditions.append("category = %s")
        params.append(category)
    if region:
        conditions.append("region = %s")
        params.append(region)
    if segment:
        conditions.append("segment = %s")
        params.append(segment)
    if market:
        conditions.append("market = %s")
        params.append(market)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params

# ── FILTROS DISPONIBLES ───────────────────────────────────────────────────────
@app.get("/api/filters", tags=["Meta"],
         summary="Obtener valores únicos para los filtros del dashboard")
def get_filters():
    """Devuelve los valores únicos de cada dimensión para construir los dropdowns."""
    years      = query("SELECT DISTINCT EXTRACT(YEAR FROM order_date)::INT AS year FROM orders ORDER BY year")
    categories = query("SELECT DISTINCT category FROM orders WHERE category IS NOT NULL ORDER BY category")
    regions    = query("SELECT DISTINCT region    FROM orders WHERE region    IS NOT NULL ORDER BY region")
    segments   = query("SELECT DISTINCT segment   FROM orders WHERE segment   IS NOT NULL ORDER BY segment")
    markets    = query("SELECT DISTINCT market    FROM orders WHERE market    IS NOT NULL ORDER BY market")

    return {
        "years":      [r["year"]     for r in years],
        "categories": [r["category"] for r in categories],
        "regions":    [r["region"]   for r in regions],
        "segments":   [r["segment"]  for r in segments],
        "markets":    [r["market"]   for r in markets],
    }

# ── KPIs ──────────────────────────────────────────────────────────────────────
@app.get("/api/kpis", tags=["Analytics"],
         summary="KPIs principales — ventas, ganancia, órdenes, margen")
def get_kpis(
    year:     Optional[str] = Query(None, description="Año fiscal"),
    category: Optional[str] = Query(None, description="Categoría de producto"),
    region:   Optional[str] = Query(None, description="Región geográfica"),
    segment:  Optional[str] = Query(None, description="Segmento de cliente"),
    market:   Optional[str] = Query(None, description="Mercado"),
):
    where, params = build_where(year, category, region, segment, market)
    return query_one(f"""
        SELECT
            ROUND(SUM(sales)::NUMERIC,   2)  AS total_sales,
            ROUND(SUM(profit)::NUMERIC,  2)  AS total_profit,
            COUNT(DISTINCT order_id)         AS total_orders,
            COUNT(*)                         AS total_rows,
            ROUND(AVG(discount)::NUMERIC, 4) AS avg_discount,
            ROUND(
                CASE WHEN SUM(sales) > 0
                THEN (SUM(profit) / SUM(sales)) * 100
                ELSE 0 END::NUMERIC, 2
            )                                AS profit_margin
        FROM orders {where}
    """, params)

# ── VENTAS POR MES ────────────────────────────────────────────────────────────
@app.get("/api/sales-by-month", tags=["Analytics"],
         summary="Ventas y ganancias agregadas por mes")
def get_sales_by_month(
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
    segment:  Optional[str] = Query(None),
    market:   Optional[str] = Query(None),
):
    where, params = build_where(year, category, region, segment, market)
    return query(f"""
        SELECT
            TO_CHAR(order_date, 'YYYY-MM') AS month,
            ROUND(SUM(sales)::NUMERIC,  2) AS sales,
            ROUND(SUM(profit)::NUMERIC, 2) AS profit,
            COUNT(DISTINCT order_id)       AS orders
        FROM orders {where}
        GROUP BY month
        ORDER BY month
    """, params)

# ── VENTAS POR CATEGORÍA ──────────────────────────────────────────────────────
@app.get("/api/sales-by-category", tags=["Analytics"],
         summary="Ventas, ganancia y unidades por categoría y subcategoría")
def get_sales_by_category(
    year:    Optional[str] = Query(None),
    region:  Optional[str] = Query(None),
    segment: Optional[str] = Query(None),
    market:  Optional[str] = Query(None),
):
    where, params = build_where(year, None, region, segment, market)
    return query(f"""
        SELECT
            category,
            sub_category,
            ROUND(SUM(sales)::NUMERIC,  2) AS sales,
            ROUND(SUM(profit)::NUMERIC, 2) AS profit,
            SUM(quantity)                  AS units,
            ROUND(
                CASE WHEN SUM(sales) > 0
                THEN (SUM(profit)/SUM(sales))*100
                ELSE 0 END::NUMERIC, 2
            ) AS margin
        FROM orders {where}
        GROUP BY category, sub_category
        ORDER BY sales DESC
    """, params)

# ── VENTAS POR REGIÓN ─────────────────────────────────────────────────────────
@app.get("/api/sales-by-region", tags=["Analytics"],
         summary="Ventas agrupadas por región y mercado")
def get_sales_by_region(
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    segment:  Optional[str] = Query(None),
):
    where, params = build_where(year, category, None, segment)
    return query(f"""
        SELECT
            region,
            market,
            ROUND(SUM(sales)::NUMERIC,  2) AS sales,
            ROUND(SUM(profit)::NUMERIC, 2) AS profit,
            COUNT(DISTINCT order_id)       AS orders,
            COUNT(DISTINCT country)        AS countries
        FROM orders {where}
        GROUP BY region, market
        ORDER BY sales DESC
    """, params)

# ── TOP PAÍSES ────────────────────────────────────────────────────────────────
@app.get("/api/top-countries", tags=["Analytics"],
         summary="Top N países por ventas")
def get_top_countries(
    limit:    int           = Query(15, ge=5, le=50, description="Número de países"),
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
):
    where, params = build_where(year, category, region)
    return query(f"""
        SELECT
            country,
            region,
            ROUND(SUM(sales)::NUMERIC,  2) AS sales,
            ROUND(SUM(profit)::NUMERIC, 2) AS profit,
            COUNT(DISTINCT order_id)       AS orders
        FROM orders {where}
        GROUP BY country, region
        ORDER BY sales DESC
        LIMIT {limit}
    """, params)

# ── TENDENCIA ANUAL ───────────────────────────────────────────────────────────
@app.get("/api/yearly-trend", tags=["Analytics"],
         summary="Tendencia de ventas y ganancia año a año")
def get_yearly_trend(
    category: Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
    segment:  Optional[str] = Query(None),
):
    where, params = build_where(None, category, region, segment)
    return query(f"""
        SELECT
            EXTRACT(YEAR FROM order_date)::INT AS year,
            ROUND(SUM(sales)::NUMERIC,  2)     AS sales,
            ROUND(SUM(profit)::NUMERIC, 2)     AS profit,
            COUNT(DISTINCT order_id)           AS orders,
            ROUND(
                CASE WHEN SUM(sales) > 0
                THEN (SUM(profit)/SUM(sales))*100
                ELSE 0 END::NUMERIC, 2
            ) AS margin
        FROM orders {where}
        GROUP BY year
        ORDER BY year
    """, params)

# ── SEGMENTOS ─────────────────────────────────────────────────────────────────
@app.get("/api/sales-by-segment", tags=["Analytics"],
         summary="Distribución de ventas por segmento de cliente")
def get_sales_by_segment(
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
):
    where, params = build_where(year, category, region)
    return query(f"""
        SELECT
            segment,
            ROUND(SUM(sales)::NUMERIC,  2) AS sales,
            ROUND(SUM(profit)::NUMERIC, 2) AS profit,
            COUNT(DISTINCT order_id)       AS orders,
            COUNT(DISTINCT customer_id)    AS customers
        FROM orders {where}
        GROUP BY segment
        ORDER BY sales DESC
    """, params)

# ── SHIP MODE ─────────────────────────────────────────────────────────────────
@app.get("/api/ship-mode", tags=["Analytics"],
         summary="Distribución por modo de envío")
def get_ship_mode(
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    where, params = build_where(year, category)
    return query(f"""
        SELECT
            ship_mode,
            COUNT(*)                            AS orders,
            ROUND(AVG(shipping_cost)::NUMERIC, 2) AS avg_cost,
            ROUND(SUM(sales)::NUMERIC, 2)       AS sales
        FROM orders {where}
        GROUP BY ship_mode
        ORDER BY orders DESC
    """, params)

# ── TABLA DE DETALLE ──────────────────────────────────────────────────────────
@app.get("/api/orders", tags=["Data"],
         summary="Tabla paginada de órdenes individuales")
def get_orders(
    page:     int           = Query(1,   ge=1,  description="Número de página"),
    per_page: int           = Query(20,  ge=5, le=100, description="Filas por página"),
    year:     Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region:   Optional[str] = Query(None),
    segment:  Optional[str] = Query(None),
):
    where, params = build_where(year, category, region, segment)
    offset = (page - 1) * per_page

    total = query_one(f"SELECT COUNT(*) AS total FROM orders {where}", params)
    rows  = query(f"""
        SELECT
            order_id, order_date, customer_name, segment,
            country, region, category, sub_category, product_name,
            ROUND(sales::NUMERIC,  2) AS sales,
            quantity,
            ROUND(profit::NUMERIC, 2) AS profit,
            ship_mode
        FROM orders {where}
        ORDER BY order_date DESC
        LIMIT {per_page} OFFSET {offset}
    """, params)

    return {
        "total":    total["total"],
        "page":     page,
        "per_page": per_page,
        "pages":    -(-total["total"] // per_page),
        "data":     rows,
    }

# ── HEALTH CHECK ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Meta"], summary="Health check")
def health():
    try:
        r = query_one("SELECT COUNT(*) AS total FROM orders")
        return {"status": "ok", "rows": r["total"]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ── FRONTEND ESTÁTICO ─────────────────────────────────────────────────────────
# Descomenta esto cuando hagas deploy en Railway (sirve el frontend también)
# app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
