import psycopg2
from psycopg2 import pool
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
# --- CONFIGURACIÓN DEL POOL ---
# Usamos st.cache_resource para que el Pool no se reinicie cada vez que cambias de pestaña
@st.cache_resource
def crear_pool_conexiones():
    """Crea un pool de conexiones persistente."""
    try:
        db = st.secrets["database"]
        # Creamos un pool que maneja entre 1 y 10 conexiones abiertas
        # Esto reduce drásticamente el tiempo de respuesta (latencia)
        return psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=db["host"],
            port=db["port"],
            database=db["database"],
            user=db["user"],
            password=db["password"],
            sslmode="require"
        )
    except Exception as e:
        st.error(f"❌ Error al crear el pool de conexiones: {e}")
        return None

# Inicializamos el pool una sola vez
connection_pool = crear_pool_conexiones()

def ejecutar_consulta(query, params=()):
    """Ejecuta INSERT, UPDATE o DELETE optimizado."""
    query = query.replace('?', '%s')
    conn = None
    if connection_pool:
        try:
            # Tomamos una conexión del pool (mucho más rápido que abrir una nueva)
            conn = connection_pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            if conn: conn.rollback()
            st.error(f"❌ Error al ejecutar consulta: {e}")
        finally:
            if conn:
                # Devolvemos la conexión al pool en lugar de cerrarla
                connection_pool.putconn(conn)

def obtener_datos(query, params=()):
    """Obtiene datos como DataFrame usando el pool."""
    query = query.replace('?', '%s')
    conn = None
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            return pd.DataFrame()
        finally:
            if conn:
                connection_pool.putconn(conn)
    return pd.DataFrame()

def validar_usuario(usuario, contrasena):
    """Valida credenciales usando el pool."""
    query = "SELECT id_usuario, nombre, rol FROM usuarios WHERE usuario = %s AND contrasena = %s"
    df = obtener_datos(query, (usuario, contrasena))
    if not df.empty:
        return df.iloc[0].to_dict()
    return None

def registrar_log(accion, tabla, detalle):
    try:
        usuario = st.session_state.get('usuario', 'Sistema')
        
        # 1. Obtenemos la hora UTC pura (la hora internacional)
        # 2. Le restamos 4 horas (Zona Horaria de Bolivia)
        # Esto garantiza que siempre sea exacto.
        ahora = datetime.utcnow() - timedelta(hours=4) 
        
        query = """
            INSERT INTO log_actividades (nombre_usuario, accion, tabla_afectada, detalle, fecha_hora) 
            VALUES (%s, %s, %s, %s, %s)
        """
        # Formateamos a string para que la base de datos no se confunda
        ahora_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
        
        ejecutar_consulta(query, (usuario, accion, tabla, detalle, ahora_str))
    except Exception as e:
        # Usamos st.write para no interrumpir el flujo visual si hay un error de log
        st.write(f"⚠️ Nota de sistema: No se pudo registrar el log ({e})")