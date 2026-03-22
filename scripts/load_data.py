"""
scripts/load_data.py
====================
Carga el dataset de Kaggle (Global Superstore) a PostgreSQL.
Ejecutar UNA sola vez antes de hacer deploy.

Uso:
    python scripts/load_data.py

Requiere:
    pip install pandas psycopg2-binary python-dotenv
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os
import re

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     os.getenv("DB_PORT",     "5432"),
    "dbname":   os.getenv("DB_NAME",     "superstore"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

CSV_PATH = os.getenv("CSV_PATH", "Global Superstore.csv")

# ── SCHEMA ────────────────────────────────────────────────────────────────────
SCHEMA = """
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    id                SERIAL PRIMARY KEY,
    row_id            INT,
    order_id          VARCHAR(50),
    order_date        DATE,
    ship_date         DATE,
    ship_mode         VARCHAR(50),
    customer_id       VARCHAR(50),
    customer_name     VARCHAR(100),
    segment           VARCHAR(50),
    city              VARCHAR(100),
    state             VARCHAR(100),
    country           VARCHAR(100),
    region            VARCHAR(50),
    market            VARCHAR(50),
    product_id        VARCHAR(50),
    category          VARCHAR(50),
    sub_category      VARCHAR(50),
    product_name      VARCHAR(255),
    sales             NUMERIC(12,2),
    quantity          INT,
    discount          NUMERIC(5,2),
    profit            NUMERIC(12,2),
    shipping_cost     NUMERIC(10,2),
    order_priority    VARCHAR(20)
);

CREATE INDEX idx_orders_date     ON orders(order_date);
CREATE INDEX idx_orders_category ON orders(category);
CREATE INDEX idx_orders_region   ON orders(region);
CREATE INDEX idx_orders_segment  ON orders(segment);
CREATE INDEX idx_orders_country  ON orders(country);
"""

def clean_col(name):
    """Normaliza nombre de columna a snake_case."""
    name = name.strip().lower()
    name = re.sub(r'[\s\-]+', '_', name)
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

def load():
    print(f"📂 Leyendo: {CSV_PATH}")
    try:
        df = pd.read_csv(CSV_PATH, encoding='latin-1')
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {CSV_PATH}")
        print("   Descárgalo de: https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset")
        print("   Luego ajusta CSV_PATH en .env o ponlo en la raíz del proyecto.")
        return

    print(f"   {len(df)} filas encontradas")

    # Limpiar columnas
    df.columns = [clean_col(c) for c in df.columns]
    print(f"   Columnas: {list(df.columns)}")

    # Mapear columnas al schema
    col_map = {
        'row_id':         'row_id',
        'order_id':       'order_id',
        'order_date':     'order_date',
        'ship_date':      'ship_date',
        'ship_mode':      'ship_mode',
        'customer_id':    'customer_id',
        'customer_name':  'customer_name',
        'segment':        'segment',
        'city':           'city',
        'state':          'state',
        'country':        'country',
        'region':         'region',
        'market':         'market',
        'product_id':     'product_id',
        'category':       'category',
        'sub_category':   'sub_category',
        'product_name':   'product_name',
        'sales':          'sales',
        'quantity':       'quantity',
        'discount':       'discount',
        'profit':         'profit',
        'shipping_cost':  'shipping_cost',
        'order_priority': 'order_priority',
    }

    # Seleccionar solo columnas disponibles
    available = {k: v for k, v in col_map.items() if k in df.columns}
    df = df.rename(columns=available)
    df = df[[c for c in col_map.values() if c in df.columns]]

    # Limpiar datos
    df['order_date'] = pd.to_datetime(df['order_date'], dayfirst=True, errors='coerce')
    df['ship_date']  = pd.to_datetime(df['ship_date'],  dayfirst=True, errors='coerce')
    df['sales']      = pd.to_numeric(df['sales'],    errors='coerce').fillna(0)
    df['profit']     = pd.to_numeric(df['profit'],   errors='coerce').fillna(0)
    df['quantity']   = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
    df['discount']   = pd.to_numeric(df['discount'], errors='coerce').fillna(0)
    df['shipping_cost'] = pd.to_numeric(df.get('shipping_cost', 0), errors='coerce').fillna(0)

    # Eliminar filas sin fecha
    df = df.dropna(subset=['order_date'])
    print(f"   {len(df)} filas limpias")

    # Conectar a PostgreSQL
    print(f"\n🔌 Conectando a PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    print("🗄️  Creando schema...")
    cur.execute(SCHEMA)
    conn.commit()

    # Insertar en lotes
    cols = [c for c in col_map.values() if c in df.columns]
    rows = [tuple(row) for row in df[cols].itertuples(index=False, name=None)]

    print(f"⬆️  Insertando {len(rows)} filas...")
    execute_values(cur,
        f"INSERT INTO orders ({', '.join(cols)}) VALUES %s",
        rows, page_size=1000
    )
    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Dataset cargado exitosamente — {len(rows)} filas en PostgreSQL")
    print("   Ya puedes arrancar el backend: uvicorn backend.main:app --reload")

if __name__ == "__main__":
    load()
