import streamlit as st
import os
import pandas as pd
from modules.database import obtener_datos

def render_ventas():
    """
    Renderiza el historial detallado de ventas consultando la base de datos en la nube.
    Versión optimizada para evitar errores de KeyError 'ID'.
    """
    # 1. Encabezado con Logo
    col_logo, col_tit = st.columns([1, 5])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=80)
    with col_tit:
        st.header("📋 Historial General de Ventas")
    
    # 2. Consulta SQL compatible con PostgreSQL (Supabase)
    # Importante: Usamos alias entre comillas "ID" para mantener el nombre exacto
    query = """
        SELECT 
            p.id_pedido as "ID", 
            COALESCE(c.nombre, 'Cliente Minorista') as "Cliente", 
            COALESCE(i.nombre, 'Producto no especificado') as "Detalle", 
            COALESCE(i.color, '-') as "Color", 
            p.cantidad as "Cant", 
            p.precio as "Total_Bs", 
            p.fecha as "Fecha_Hora"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        ORDER BY p.fecha DESC
    """
    
    try:
        df = obtener_datos(query)
        
        if not df.empty:
            # --- LIMPIEZA Y FORMATEO DE DATOS ---
            # Aseguramos que la columna ID sea tratada como texto para evitar comas en números grandes
            df['ID'] = df['ID'].astype(str)
            
            # Convertimos a datetime de forma segura
            df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'])
            fecha_display = df['Fecha_Hora'].dt.strftime('%d/%m/%Y %H:%M')
            
            # Convertimos precios a float para cálculos
            df['Total_Bs'] = pd.to_numeric(df['Total_Bs'], errors='coerce').fillna(0.0)
            
            # 3. Métricas Resumen
            total_ventas = df['Total_Bs'].sum()
            cant_pedidos = len(df)
            
            m1, m2 = st.columns(2)
            m1.metric("Ventas Totales Registradas", f"{total_ventas:,.2f} Bs")
            m2.metric("Cantidad de Pedidos", f"{cant_pedidos} registros")

            

            # 4. Visualización de Tabla
            # Creamos una copia para mostrar con los nombres de columna bonitos
            df_display = df.copy()
            df_display['Fecha y Hora'] = fecha_display
            
            # Reordenar y renombrar para el usuario
            df_mostrar = df_display[['ID', 'Cliente', 'Detalle', 'Color', 'Cant', 'Total_Bs', 'Fecha y Hora']]
            
            st.dataframe(
                df_mostrar, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Total_Bs": st.column_config.NumberColumn("Total (Bs)", format="%.2f Bs"),
                    "ID": st.column_config.TextColumn("Nro Pedido"),
                    "Cant": st.column_config.NumberColumn("Cantidad")
                }
            )
            
            st.caption("✨ Sincronizado con la base de datos central en la nube.")
            
        else:
            st.info("✨ No se encontraron registros de ventas en la base de datos.")
            
    except Exception as e:
        st.error(f"⚠️ Error de conexión: No se pudo cargar el historial. Detalles: {e}")