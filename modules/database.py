import sqlite3
import pandas as pd

DB_PATH = "sistema_ventas.db"

def sincronizar_bd():
    """Asegura que la tabla inventario tenga la estructura para las nuevas líneas y la hora."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Crear tabla con la estructura completa desde el inicio
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                linea TEXT,
                tamano TEXT,
                color TEXT,
                cantidad INTEGER DEFAULT 0,
                precio_venta REAL DEFAULT 0.0,
                fecha_actualizacion TEXT
            )
        """)
        
        # 2. Lista de columnas necesarias para el nuevo sistema
        # Añadimos 'fecha_actualizacion' para que guarde la hora de tu Mac
        columnas = [
            ("linea", "TEXT"), 
            ("tamano", "TEXT"), 
            ("precio_venta", "REAL DEFAULT 0.0"),
            ("fecha_actualizacion", "TEXT")
        ]
        
        for col_nombre, col_tipo in columnas:
            try:
                cursor.execute(f"ALTER TABLE inventario ADD COLUMN {col_nombre} {col_tipo}")
            except: 
                # Si la columna ya existe, SQLite dará error y simplemente la saltamos
                pass
        
        conn.commit()

# Ejecutar sincronización al cargar el módulo
sincronizar_bd()

def ejecutar_consulta(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def obtener_datos(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        # Usamos pandas para leer los resultados de forma sencilla
        return pd.read_sql_query(query, conn, params=params)

def validar_usuario(usuario, contrasena):
    query = "SELECT id_usuario, nombre, rol FROM usuarios WHERE usuario = ? AND contrasena = ?"
    df = obtener_datos(query, (usuario, contrasena))
    return df.iloc[0].to_dict() if not df.empty else None