import streamlit as st
import pandas as pd
import time
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

# --- FUNCIONES DE EXPORTACIÓN CORREGIDAS ---

def exportar_inventario_pdf(df):
    # Usamos Helvetica por compatibilidad universal
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE DE INVENTARIO - FABRICA DE MEDIAS", ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(35, 10, "Linea", 1, 0, 'C', True)
    pdf.cell(50, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(35, 10, "Color", 1, 0, 'C', True)
    pdf.cell(25, 10, "Stock", 1, 0, 'C', True)
    pdf.cell(30, 10, "Precio", 1, 1, 'C', True)
    
    # Datos
    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        pdf.cell(15, 10, str(row['ID']), 1)
        pdf.cell(35, 10, str(row['Línea']), 1)
        pdf.cell(50, 10, str(row['Tipo'])[:25], 1)
        pdf.cell(35, 10, str(row['Color']), 1)
        pdf.cell(25, 10, str(row['Cantidad']), 1)
        pdf.cell(30, 10, f"{row['Precio']:.2f} Bs", 1)
        pdf.ln()
    
    # --- SOLUCIÓN UNIVERSAL PARA PDF ---
    resultado = pdf.output(dest='S')
    if isinstance(resultado, (bytes, bytearray)):
        return bytes(resultado)
    return resultado.encode('latin-1', errors='replace')

def exportar_ventas_pdf(df, fecha_inicio, fecha_fin):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE GENERAL DE VENTAS", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(200, 10, txt=f"Periodo: {fecha_inicio} al {fecha_fin}", ln=True, align='C')
    pdf.ln(5)
    
    # Encabezados
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(45, 10, "Cliente", 1, 0, 'C', True)
    pdf.cell(45, 10, "Producto", 1, 0, 'C', True)
    pdf.cell(20, 10, "Cant.", 1, 0, 'C', True)
    pdf.cell(30, 10, "Total (Bs)", 1, 0, 'C', True)
    pdf.cell(35, 10, "Fecha", 1, 1, 'C', True)
    
    # Datos
    pdf.set_font("Helvetica", size=8)
    total_acumulado = 0
    for _, row in df.iterrows():
        pdf.cell(15, 9, str(row['ID']), 1)
        pdf.cell(45, 9, str(row['Cliente'])[:25], 1)
        pdf.cell(45, 9, str(row['Producto'])[:25], 1)
        pdf.cell(20, 9, str(row['Cant']), 1)
        pdf.cell(30, 9, f"{row['Total']:.2f}", 1)
        pdf.cell(35, 9, str(row['Fecha'])[:10], 1)
        pdf.ln()
        total_acumulado += float(row['Total'])
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(125, 10, "INGRESOS TOTALES EN EL PERIODO", 1, 0, 'R', True)
    pdf.cell(65, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'C', True)
        
    # --- SOLUCIÓN UNIVERSAL PARA PDF ---
    resultado = pdf.output(dest='S')
    if isinstance(resultado, (bytes, bytearray)):
        return bytes(resultado)
    return resultado.encode('latin-1', errors='replace')

# --- RENDERIZADO DEL PANEL ---

def render_reportes():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)
    with col_titulo:
        st.header("📊 Panel de Reportes")

    st.sidebar.subheader("📅 Filtro de Fecha")
    f_inicio = st.sidebar.date_input("Fecha Inicio", date.today().replace(day=1))
    f_fin = st.sidebar.date_input("Fecha Fin", date.today())

    # 1. Resumen de Cifras
    st.subheader(f"📈 Resumen del periodo: {f_inicio} a {f_fin}")
    col1, col2, col3 = st.columns(3)
    
    query_total = "SELECT SUM(precio) as total FROM pedidos WHERE date(fecha) BETWEEN ? AND ?"
    ventas_data = obtener_datos(query_total, (f_inicio, f_fin))
    ventas_periodo = ventas_data.iloc[0]['total'] if not ventas_data.empty and ventas_data.iloc[0]['total'] else 0
    
    cant_clientes = obtener_datos("SELECT COUNT(*) as total FROM clientes").iloc[0]['total'] or 0
    stock_bajo = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10").iloc[0]['total'] or 0
    
    col1.metric("Ingresos en Periodo", f"{ventas_periodo:.2f} Bs")
    col2.metric("Clientes Registrados", cant_clientes)
    col3.metric("Alertas Stock Bajo", stock_bajo)
    
    # 2. Reporte de Inventario
    st.markdown("---")
    with st.expander("📦 Ver Estado del Inventario"):
        df_inv = obtener_datos("""
            SELECT id as ID, linea as Línea, tamano as Tipo, color as Color, 
                   cantidad as Cantidad, precio_venta as Precio 
            FROM inventario
        """)
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True)
            try:
                pdf_inv = exportar_inventario_pdf(df_inv)
                st.download_button(
                    label="📥 Descargar Inventario Actual (PDF)", 
                    data=pdf_inv, 
                    file_name=f"stock_{date.today()}.pdf", 
                    mime="application/pdf",
                    key="btn_inv_pdf"
                )
            except Exception as e:
                st.error(f"Error PDF Inventario: {e}")

    # 3. Reporte de Ventas
    st.markdown("---")
    st.subheader("💰 Historial de Ventas Filtrado")
    
    query_ventas = """
        SELECT p.id_pedido as ID, c.nombre as Cliente, i.nombre as Producto, 
               p.cantidad as Cant, p.precio as Total, p.fecha as Fecha
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        WHERE date(p.fecha) BETWEEN ? AND ?
        ORDER BY p.fecha DESC
    """
    df_ventas = obtener_datos(query_ventas, (f_inicio, f_fin))
    
    if not df_ventas.empty:
        st.dataframe(df_ventas, use_container_width=True)
        try:
            pdf_ventas = exportar_ventas_pdf(df_ventas, f_inicio, f_fin)
            st.download_button(
                label="📥 Descargar Reporte de Ventas (PDF)", 
                data=pdf_ventas, 
                file_name=f"ventas_{f_inicio}_{f_fin}.pdf", 
                mime="application/pdf",
                key="btn_ventas_pdf"
            )
        except Exception as e:
            st.error(f"Error PDF Ventas: {e}")

        # 4. Análisis Visual
        st.markdown("---")
        st.subheader("📊 Análisis Visual de Ventas")

        df_ventas['Fecha_dt'] = df_ventas['Fecha'].str[:10]
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown("##### 📈 Tendencia de Ingresos (Bs)")
            ventas_diarias = df_ventas.groupby('Fecha_dt')['Total'].sum()
            st.line_chart(ventas_diarias)
            
        with col_der:
            st.markdown("##### 🏆 Top Clientes (Por Compra)")
            top_clientes = df_ventas.groupby('Cliente')['Total'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_clientes)

    else:
        st.info("💡 No hay datos suficientes para generar reportes en este periodo.")