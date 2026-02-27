import streamlit as st
import pandas as pd
import time
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

# --- FUNCIONES DE EXPORTACIÓN (PDF) ---

def exportar_inventario_pdf(df):
    """Genera un archivo PDF del inventario actual."""
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE DE INVENTARIO - FABRICA DE MEDIAS", ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados de tabla
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(35, 10, "Linea", 1, 0, 'C', True)
    pdf.cell(50, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(35, 10, "Color", 1, 0, 'C', True)
    pdf.cell(25, 10, "Stock", 1, 0, 'C', True)
    pdf.cell(30, 10, "Precio", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        pdf.cell(15, 10, str(row['ID']), 1)
        pdf.cell(35, 10, str(row['Línea']), 1)
        pdf.cell(50, 10, str(row['Tipo'])[:25], 1)
        pdf.cell(35, 10, str(row['Color']), 1)
        pdf.cell(25, 10, str(row['Cantidad']), 1)
        pdf.cell(30, 10, f"{float(row['Precio'] or 0):.2f} Bs", 1)
        pdf.ln()
    
    # Manejo de salida compatible con Streamlit Cloud
    resultado = pdf.output(dest='S')
    if isinstance(resultado, str):
        return resultado.encode('latin-1', errors='replace')
    return bytes(resultado)

def exportar_ventas_pdf(df, fecha_inicio, fecha_fin):
    """Genera un reporte detallado de ventas en PDF."""
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE GENERAL DE VENTAS", ln=True, align='C')
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(200, 10, txt=f"Periodo: {fecha_inicio} al {fecha_fin}", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(45, 10, "Cliente", 1, 0, 'C', True)
    pdf.cell(45, 10, "Producto", 1, 0, 'C', True)
    pdf.cell(20, 10, "Cant.", 1, 0, 'C', True)
    pdf.cell(30, 10, "Total (Bs)", 1, 0, 'C', True)
    pdf.cell(35, 10, "Fecha", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", size=8)
    total_acumulado = 0
    for _, row in df.iterrows():
        total_fila = float(row['Total'] or 0)
        pdf.cell(15, 9, str(row['ID']), 1)
        pdf.cell(45, 9, str(row['Cliente'])[:25], 1)
        pdf.cell(45, 9, str(row['Producto'])[:25], 1)
        pdf.cell(20, 9, str(row['Cant']), 1)
        pdf.cell(30, 9, f"{total_fila:.2f}", 1)
        pdf.cell(35, 9, str(row['Fecha'])[:10], 1)
        pdf.ln()
        total_acumulado += total_fila
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(125, 10, "INGRESOS TOTALES EN EL PERIODO", 1, 0, 'R', True)
    pdf.cell(65, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'C', True)
        
    resultado = pdf.output(dest='S')
    if isinstance(resultado, str):
        return resultado.encode('latin-1', errors='replace')
    return bytes(resultado)

# --- FUNCIÓN PRINCIPAL DE RENDERIZADO ---

def render_reportes():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)
    with col_titulo:
        st.header("📊 Dashboard de Gestión ")

    # Filtros laterales
    st.sidebar.subheader("📅 Rango de Análisis")
    f_inicio = st.sidebar.date_input("Desde", date.today().replace(day=1))
    f_fin = st.sidebar.date_input("Hasta", date.today())

    # 1. KPIs principales
    st.subheader(f"📈 Resumen Ejecutivo: {f_inicio.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')}")
    
    # Consulta de ventas totales
    v_query = "SELECT SUM(precio) as total FROM pedidos WHERE fecha::date BETWEEN %s AND %s"
    v_data = obtener_datos(v_query, (f_inicio, f_fin))
    ventas_periodo = float(v_data.iloc[0]['total'] or 0)
    
    # Consultas rápidas para métricas
    cli_data = obtener_datos("SELECT COUNT(*) as total FROM clientes")
    stock_data = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Ventas en Periodo", f"{ventas_periodo:.2f} Bs")
    m2.metric("👥 Total Clientes", int(cli_data.iloc[0]['total'] or 0))
    m3.metric("⚠️ Productos en Alerta", int(stock_data.iloc[0]['total'] or 0))
    
    # 2. SECCIÓN DE INVENTARIO
    st.markdown("---")
    with st.expander("📦 Consultar Inventario Actual y Exportar"):
        # Aseguramos Alias con comillas dobles para evitar KeyError 'ID'
        df_inv = obtener_datos("""
            SELECT id as "ID", linea as "Línea", tamano as "Tipo", color as "Color", 
                   cantidad as "Cantidad", precio_venta as "Precio" 
            FROM inventario
            ORDER BY cantidad ASC
        """)
        
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
            if st.button("📄 Generar PDF de Inventario"):
                pdf_bytes = exportar_inventario_pdf(df_inv)
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"inventario_{date.today()}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("No hay productos en el inventario.")

    # 3. SECCIÓN DE VENTAS DETALLADAS
    st.markdown("---")
    st.subheader("💰 Historial de Movimientos")
    
    # Consulta con JOIN y Alias exactos
    query_ventas = """
        SELECT p.id_pedido as "ID", 
               COALESCE(c.nombre, 'Venta Directa') as "Cliente", 
               COALESCE(i.nombre, 'Producto Borrado') as "Producto", 
               p.cantidad as "Cant", 
               p.precio as "Total", 
               p.fecha as "Fecha"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        WHERE p.fecha::date BETWEEN %s AND %s
        ORDER BY p.fecha DESC
    """
    df_ventas = obtener_datos(query_ventas, (f_inicio, f_fin))
    
    if not df_ventas.empty:
        # Formateo para la tabla
        df_ventas['Fecha_Visual'] = pd.to_datetime(df_ventas['Fecha']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            df_ventas[['ID', 'Cliente', 'Producto', 'Cant', 'Total', 'Fecha_Visual']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Botón para descargar reporte de ventas
        if st.button("📄 Generar Reporte de Ventas PDF"):
            pdf_v_bytes = exportar_ventas_pdf(df_ventas, f_inicio, f_fin)
            st.download_button(
                label="📥 Descargar Reporte de Ventas", 
                data=pdf_v_bytes, 
                file_name=f"ventas_{f_inicio}_{f_fin}.pdf", 
                mime="application/pdf"
            )

        # 4. GRÁFICOS ESTADÍSTICOS
        st.markdown("---")
        st.subheader("📊 Análisis de Tendencias")
        
        df_ventas['Fecha_Plot'] = pd.to_datetime(df_ventas['Fecha']).dt.date
        
        c_izq, c_der = st.columns(2)
        with c_izq:
            st.write("**Evolución Diaria de Ingresos (Bs)**")
            evolucion = df_ventas.groupby('Fecha_Plot')['Total'].sum()
            st.line_chart(evolucion)
            
        with c_der:
            st.write("**Top 5 Clientes por Volumen de Compra**")
            top_c = df_ventas.groupby('Cliente')['Total'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_c)
    else:
        st.info("No se encontraron ventas para el rango seleccionado.")