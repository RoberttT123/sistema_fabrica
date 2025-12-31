import streamlit as st
import os
from modules.database import obtener_datos

def render_ventas():
    # Logo en la parte superior del historial
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
        
    st.header("📋 Historial de Ventas")
    
    # Consulta robusta que une las tablas
    query = """
        SELECT 
            p.id_pedido as ID, 
            c.nombre as Cliente, 
            i.nombre as Detalle, 
            i.color as Color, 
            p.cantidad as Cant, 
            p.precio as Total, 
            p.fecha as Fecha
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        ORDER BY p.id_pedido DESC
    """
    
    df = obtener_datos(query)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No hay registros de ventas. Realiza un pedido para ver datos aquí.")