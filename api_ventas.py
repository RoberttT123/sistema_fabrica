from fastapi import FastAPI, HTTPException
from modules.database import obtener_datos
import uvicorn
from typing import Optional
import os
import pandas as pd

app = FastAPI(
    title="API Fábrica de Medias - Cloud Edition",
    description="Servidor de datos en la nube conectado a PostgreSQL (Supabase)",
    version="4.0"
)

@app.get("/")
def inicio():
    """Endpoint de verificación de salud de la API."""
    return {
        "status": "online", 
        "server": "Cloud Production",
        "database": "PostgreSQL/Supabase",
        "mensaje": "API sincronizada y lista para servir datos de inventario."
    }

@app.get("/productos")
def listar_productos(
    linea: Optional[str] = None, 
    tamano: Optional[str] = None, 
    color: Optional[str] = None
):
    """
    Obtiene los productos de la tabla 'inventario' en la nube.
    Soporta filtrado dinámico para Lycra, Panty y Stretch.
    """
    # ADAPTACIÓN POSTGRES: Usamos COALESCE en lugar de IFNULL
    # Usamos %s como placeholder para parámetros
    query = """
        SELECT 
            id, 
            nombre, 
            COALESCE(linea, 'Lycra') as linea, 
            COALESCE(tamano, 'Soporte Lycra') as tamano, 
            color, 
            cantidad as stock, 
            precio_venta,
            CONCAT('Medias de alta calidad - ', COALESCE(linea, 'General')) as descripcion
        FROM inventario 
        WHERE cantidad > 0
    """
    params = []

    # Aplicación de filtros dinámicos (Sintaxis compatible con Postgres)
    if linea and linea != "Todos":
        query += " AND linea = %s"
        params.append(linea)
    
    if tamano and tamano != "Todos":
        query += " AND tamano = %s"
        params.append(tamano)

    if color and color != "Todos":
        query += " AND color = %s"
        params.append(color)

    query += " ORDER BY linea ASC, nombre ASC"

    try:
        # La función obtener_datos de tu nuevo modules/database.py 
        # ya maneja la conexión a Supabase
        df = obtener_datos(query, tuple(params))

        if df.empty:
            return []

        # Limpieza de datos avanzada para asegurar JSON válido
        df['precio_venta'] = df['precio_venta'].fillna(0.0)
        df['color'] = df['color'].fillna("Sin Color")
        df['stock'] = df['stock'].fillna(0).astype(int)

        return df.to_dict(orient="records")

    except Exception as e:
        # Log del error en el servidor (opcional)
        print(f"Error API: {e}")
        raise HTTPException(status_code=500, detail="Error interno al consultar la base de datos en la nube.")

@app.get("/estado_stock/{id_producto}")
def verificar_stock(id_producto: int):
    """Consulta rápida de stock por ID para integraciones externas."""
    query = "SELECT nombre, cantidad as stock FROM inventario WHERE id = %s"
    try:
        df = obtener_datos(query, (id_producto,))
        if df.empty:
            raise HTTPException(status_code=404, detail="Producto no encontrado en el inventario.")
        
        resultado = df.to_dict(orient="records")[0]
        resultado['stock'] = int(resultado['stock'])
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os  # <--- Asegúrate de que esta línea esté aquí
    # Intento de limpiar el puerto 8001
    try:
        if os.name != 'nt': # Solo para Mac/Linux
            os.system("lsof -t -i tcp:8001 | xargs kill -9 > /dev/null 2>&1")
    except:
        pass

    print("🚀 Iniciando API en http://0.0.0.0:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")   