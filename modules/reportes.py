import streamlit as st
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

def exportar_inventario_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE DE INVENTARIO ACTUAL", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(10, 10, "ID", 1)
    pdf.cell(80, 10, "Detalle", 1)
    pdf.cell(40, 10, "Color", 1)
    pdf.cell(30, 10, "Stock", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for index, row in df.iterrows():
        pdf.cell(10, 10, str(row['ID']), 1)
        pdf.cell(80, 10, str(row['Detalle']), 1)
        pdf.cell(40, 10, str(row['Color']), 1)
        pdf.cell(30, 10, str(row['Cantidad']), 1)
        pdf.ln()
    return bytes(pdf.output())

def exportar_ventas_pdf(df, fecha_inicio, fecha_fin):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE GENERAL DE VENTAS", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 10, txt=f"Periodo: {fecha_inicio} al {fecha_fin}", ln=True, align='C')
    pdf.ln(5)
    
    # Encabezados
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(15, 10, "ID", 1)
    pdf.cell(45, 10, "Cliente", 1)
    pdf.cell(45, 10, "Producto", 1)
    pdf.cell(20, 10, "Cant.", 1)
    pdf.cell(30, 10, "Total (Bs)", 1)
    pdf.cell(35, 10, "Fecha", 1)
    pdf.ln()
    
    # Datos
    pdf.set_font("Arial", size=9)
    total_acumulado = 0
    for index, row in df.iterrows():
        pdf.cell(15, 10, str(row['ID']), 1)
        pdf.cell(45, 10, str(row['Cliente'])[:25], 1)
        pdf.cell(45, 10, str(row['Producto'])[:25], 1)
        pdf.cell(20, 10, str(row['Cant']), 1)
        pdf.cell(30, 10, f"{row['Total']:.2f}", 1)
        pdf.cell(35, 10, str(row['Fecha'])[:10], 1) # Solo fecha, sin hora
        pdf.ln()
        total_acumulado += float(row['Total'])
    
    # Total al final
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(125, 10, "INGRESOS TOTALES EN EL PERIODO", 1, 0, 'R')
    pdf.cell(65, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'C')
        
    return bytes(pdf.output())

def render_reportes():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)
    with col_titulo:
        st.header("📊 Panel de Reportes")

    # --- FILTRO DE FECHAS ---
    st.sidebar.subheader("📅 Filtro de Fecha")
    f_inicio = st.sidebar.date_input("Fecha Inicio", date.today().replace(day=1))
    f_fin = st.sidebar.date_input("Fecha Fin", date.today())

    # 1. Resumen de Cifras (Filtrado)
    st.subheader(f"📈 Resumen del periodo: {f_inicio} a {f_fin}")
    col1, col2, col3 = st.columns(3)
    
    query_total = "SELECT SUM(precio) as total FROM pedidos WHERE date(fecha) BETWEEN ? AND ?"
    ventas_periodo = obtener_datos(query_total, (f_inicio, f_fin)).iloc[0]['total'] or 0
    
    cant_clientes = obtener_datos("SELECT COUNT(*) as total FROM clientes").iloc[0]['total'] or 0
    stock_bajo = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10").iloc[0]['total'] or 0
    
    col1.metric("Ingresos en Periodo", f"{ventas_periodo} Bs")
    col2.metric("Clientes Registrados", cant_clientes)
    col3.metric("Alertas Stock Bajo", stock_bajo)
    
    # 2. Reporte de Inventario (Siempre actual)
    st.markdown("---")
    with st.expander("📦 Ver Estado del Inventario"):
        df_inv = obtener_datos("SELECT id as ID, nombre as Detalle, color as Color, cantidad as Cantidad FROM inventario")
        st.dataframe(df_inv, use_container_width=True)
        if st.button("📥 Descargar Inventario Actual (PDF)"):
            pdf_inv = exportar_inventario_pdf(df_inv)
            st.download_button("Click para descargar", pdf_inv, "reporte_stock.pdf", "application/pdf")

    # 3. REPORTE DE VENTAS CON FILTRO
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
    st.dataframe(df_ventas, use_container_width=True)
    
    if st.button("📥 Descargar Reporte de Ventas Filtrado (PDF)"):
        if not df_ventas.empty:
            pdf_ventas = exportar_ventas_pdf(df_ventas, f_inicio, f_fin)
            st.download_button("Click para descargar Reporte", pdf_ventas, f"ventas_{f_inicio}_al_{f_fin}.pdf", "application/pdf")
        else:
            st.warning("No hay ventas en este rango de fechas.")

    # 4. Gráfico de Ventas Filtrado
    if not df_ventas.empty:
        st.markdown("---")
        st.subheader("📈 Rendimiento de Ventas en el periodo")
        df_grafico = df_ventas[['Fecha', 'Total']].copy()
        df_grafico['Fecha'] = df_grafico['Fecha'].str[:10] # Quedarse solo con YYYY-MM-DD
        st.line_chart(df_grafico.set_index('Fecha'))