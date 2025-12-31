import sqlite3
import pandas as pd

DB_PATH = "sistema_ventas.db"

def sincronizar_bd():
    """Repara la estructura de la base de datos automáticamente."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Columna color para inventario
        try:
            cursor.execute("ALTER TABLE inventario ADD COLUMN color TEXT")
        except: pass
        
        # Columna id_inventario para pedidos
        try:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN id_inventario INTEGER")
        except: pass
        conn.commit()

# Ejecutar sincronización al cargar
sincronizar_bd()

def ejecutar_consulta(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def obtener_datos(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

def validar_usuario(usuario, contrasena):
    query = "SELECT id_usuario, nombre, rol FROM usuarios WHERE usuario = ? AND contrasena = ?"
    df = obtener_datos(query, (usuario, contrasena))
    return df.iloc[0].to_dict() if not df.empty else None