from fastapi import FastAPI, HTTPException
from modules.database import obtener_datos
import uvicorn
from typing import Optional

app = FastAPI(
    title="API Fábrica de Medias - Sincronizada",
    description="Servidor de datos conectado a la tabla Inventario (Lycra, Panty, Stretch)",
    version="3.0"
)

@app.get("/")
def inicio():
    return {"status": "conectado", "mensaje": "API sincronizada con nuevas categorías de inventario"}

@app.get("/productos")
def listar_productos(
    linea: Optional[str] = None, 
    tamano: Optional[str] = None, 
    color: Optional[str] = None
):
    """
    Obtiene los productos de la tabla 'inventario'.
    Filtra por las nuevas líneas: Lycra, Panty, Stretch.
    """
    # Cambiamos los valores por defecto de IFNULL para que coincidan con tus nuevas líneas
    query = """
        SELECT 
            id, 
            nombre, 
            IFNULL(linea, 'Lycra') as linea, 
            IFNULL(tamano, 'Soporte Lycra') as tamano, 
            color, 
            cantidad as stock, 
            precio_venta,
            'Medias de alta calidad - ' || linea as descripcion
        FROM inventario 
        WHERE cantidad > 0
    """
    params = []

    # Aplicación de filtros dinámicos
    if linea and linea != "Todos":
        query += " AND linea = ?"
        params.append(linea)
    
    if tamano and tamano != "Todos":
        query += " AND tamano = ?"
        params.append(tamano)

    if color and color != "Todos":
        query += " AND color = ?"
        params.append(color)

    try:
        df = obtener_datos(query, tuple(params))

        if df.empty:
            return []

        # Limpieza de datos: asegurar que el JSON no lleve valores None que rompan el catálogo
        df['precio_venta'] = df['precio_venta'].fillna(0.0)
        df['color'] = df['color'].fillna("Sin Color")

        return df.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")

@app.get("/estado_stock/{id_producto}")
def verificar_stock(id_producto: int):
    """Consulta rápida de stock por ID."""
    df = obtener_datos("SELECT nombre, cantidad as stock FROM inventario WHERE id = ?", (id_producto,))
    if df.empty:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return df.to_dict(orient="records")[0]

if __name__ == "__main__":
    # Intento de limpiar el puerto 8001 antes de iniciar (Solo para Mac/Linux)
    try:
        os.system("fuser -k 8001/tcp > /dev/null 2>&1") 
    except:
        pass

    print("🚀 Iniciando API en http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")