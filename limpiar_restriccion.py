import streamlit as st
from modules.database import obtener_datos

def render_ventas():
    st.header("📋 Historial de Ventas Realizadas")

    # Esta consulta es a "prueba de fallos"
    query = """
        SELECT 
            p.id_pedido as ID, 
            IFNULL(c.nombre, 'Cliente no registrado') as Cliente, 
            IFNULL(i.nombre, 'Producto no identificado') as Detalle, 
            IFNULL(i.color, '-') as Color, 
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
        st.success(f"Se encontraron {len(df)} registros de ventas.")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("⚠️ El historial sigue vacío.")
        st.info("Revisa si al registrar el pedido se guardó el id_inventario correctamente.")