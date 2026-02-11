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
    
    # Encabezados
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(20, 10, "ID", 1)
    pdf.cell(90, 10, "Detalle", 1)
    pdf.cell(40, 10, "Color", 1)
    pdf.cell(30, 10, "Stock", 1)
    pdf.ln()
    
    # Datos
    pdf.set_font("Arial", size=10)
    for index, row in df.iterrows():
        pdf.cell(20, 10, str(row['ID']), 1)
        pdf.cell(90, 10, str(row['Detalle']), 1)
        pdf.cell(40, 10, str(row['Color']), 1)
        pdf.cell(30, 10, str(row['Cantidad']), 1)
        pdf.ln()
    
    # CORRECCIÓN AQUÍ: Retornar como bytes directamente
    return pdf.output(dest='S').encode('latin-1')

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
        pdf.cell(35, 10, str(row['Fecha'])[:10], 1)
        pdf.ln()
        total_acumulado += float(row['Total'])
    
    # Total al final
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(125, 10, "INGRESOS TOTALES EN EL PERIODO", 1, 0, 'R')
    pdf.cell(65, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'C')
        
    # CORRECCIÓN AQUÍ: Retornar como bytes directamente
    return pdf.output(dest='S').encode('latin-1')

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

    # 1. Resumen de Cifras
    st.subheader(f"📈 Resumen del periodo: {f_inicio} a {f_fin}")
    col1, col2, col3 = st.columns(3)
    
    query_total = "SELECT SUM(precio) as total FROM pedidos WHERE date(fecha) BETWEEN ? AND ?"
    ventas_data = obtener_datos(query_total, (f_inicio, f_fin))
    ventas_periodo = ventas_data.iloc[0]['total'] if not ventas_data.empty and ventas_data.iloc[0]['total'] else 0
    
    cant_clientes = obtener_datos("SELECT COUNT(*) as total FROM clientes").iloc[0]['total'] or 0
    stock_bajo = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10").iloc[0]['total'] or 0
    
    col1.metric("Ingresos en Periodo", f"{ventas_periodo} Bs")
    col2.metric("Clientes Registrados", cant_clientes)
    col3.metric("Alertas Stock Bajo", stock_bajo)
    
    # 2. Reporte de Inventario
    st.markdown("---")
    with st.expander("📦 Ver Estado del Inventario"):
        df_inv = obtener_datos("SELECT id as ID, nombre as Detalle, color as Color, cantidad as Cantidad FROM inventario")
        st.dataframe(df_inv, use_container_width=True)
        if st.button("📥 Descargar Inventario Actual (PDF)"):
            pdf_inv = exportar_inventario_pdf(df_inv)
            st.download_button(
                label="Click para descargar", 
                data=pdf_inv, 
                file_name="reporte_stock.pdf", 
                mime="application/pdf"
            )

    # 3. REPORTE DE VENTAS
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
            st.download_button(
                label="Click para descargar Reporte", 
                data=pdf_ventas, 
                file_name=f"ventas_{f_inicio}_al_{f_fin}.pdf", 
                mime="application/pdf"
            )
        else:
            st.warning("No hay ventas en este rango de fechas.")

# 4. DASHBOARD VISUAL DE RENDIMIENTO
    if not df_ventas.empty:
        st.markdown("---")
        st.subheader("📊 Análisis Visual de Ventas")

        # Preparación de datos
        df_ventas['Fecha'] = df_ventas['Fecha'].str[:10]
        
        # Fila 1: Tendencia Temporal e Ingresos por Cliente
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown("##### 📈 Tendencia de Ingresos (Bs)")
            # Agrupamos por fecha para sumar ventas del mismo día
            ventas_diarias = df_ventas.groupby('Fecha')['Total'].sum()
            st.line_chart(ventas_diarias)
            
        with col_der:
            st.markdown("##### 🏆 Top Clientes (Por Compra)")
            # Quién ha gastado más en el periodo
            top_clientes = df_ventas.groupby('Cliente')['Total'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_clientes)

        # Fila 2: Análisis de Productos
        st.markdown("---")
        col_prod1, col_prod2 = st.columns([2, 1])
        
        with col_prod1:
            st.markdown("##### 🧦 Volumen de Ventas por Producto (Unidades)")
            # Qué productos rotan más
            productos_populares = df_ventas.groupby('Producto')['Cant'].sum().sort_values(ascending=True)
            st.bar_chart(productos_populares, horizontal=True) # Gráfico horizontal para leer mejor los nombres
            
        with col_prod2:
            st.markdown("##### 💎 Resumen de Cantidades")
            # Una tabla comparativa rápida
            resumen_tabla = df_ventas.groupby('Producto').agg({
                'Cant': 'sum',
                'Total': 'sum'
            }).rename(columns={'Cant': 'Unidades', 'Total': 'Monto (Bs)'})
            st.dataframe(resumen_tabla, use_container_width=True)

    else:
        st.info("💡 No hay datos suficientes para generar gráficos en este periodo.")













import streamlit as st
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

# --- FUNCIONES DE EXPORTACIÓN ---

def exportar_inventario_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="REPORTE DE INVENTARIO - FÁBRICA DE MEDIAS", ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados adaptados a la nueva estructura
    pdf.set_font("Arial", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(35, 10, "Linea", 1, 0, 'C', True)
    pdf.cell(50, 10, "Tipo", 1, 0, 'C', True)
    pdf.cell(35, 10, "Color", 1, 0, 'C', True)
    pdf.cell(25, 10, "Stock", 1, 0, 'C', True)
    pdf.cell(30, 10, "Precio", 1, 1, 'C', True)
    
    # Datos
    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        pdf.cell(15, 10, str(row['ID']), 1)
        pdf.cell(35, 10, str(row['Línea']), 1)
        pdf.cell(50, 10, str(row['Tipo'])[:25], 1)
        pdf.cell(35, 10, str(row['Color']), 1)
        pdf.cell(25, 10, str(row['Cantidad']), 1)
        pdf.cell(30, 10, f"{row['Precio']:.2f} Bs", 1)
        pdf.ln()
    
    # Usamos latin-1 para compatibilidad con FPDF estándar
    return pdf.output(dest='S').encode('latin-1', errors='replace')

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
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(15, 10, "ID", 1, 0, 'C', True)
    pdf.cell(45, 10, "Cliente", 1, 0, 'C', True)
    pdf.cell(45, 10, "Producto", 1, 0, 'C', True)
    pdf.cell(20, 10, "Cant.", 1, 0, 'C', True)
    pdf.cell(30, 10, "Total (Bs)", 1, 0, 'C', True)
    pdf.cell(35, 10, "Fecha", 1, 1, 'C', True)
    
    # Datos
    pdf.set_font("Arial", size=8)
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
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(125, 10, "INGRESOS TOTALES EN EL PERIODO", 1, 0, 'R', True)
    pdf.cell(65, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'C', True)
        
    return pdf.output(dest='S').encode('latin-1', errors='replace')

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
    # Alerta según tu nueva tabla de inventario
    stock_bajo = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10").iloc[0]['total'] or 0
    
    col1.metric("Ingresos en Periodo", f"{ventas_periodo:.2f} Bs")
    col2.metric("Clientes Registrados", cant_clientes)
    col3.metric("Alertas Stock Bajo", stock_bajo)
    
    # 2. Reporte de Inventario (Actualizado con Linea y Tipo)
    st.markdown("---")
    with st.expander("📦 Ver Estado del Inventario (Lycra, Panty, Stretch)"):
        # Ajustamos la consulta para traer los campos nuevos
        df_inv = obtener_datos("""
            SELECT id as ID, linea as Línea, tamano as Tipo, color as Color, 
                   cantidad as Cantidad, precio_venta as Precio 
            FROM inventario
        """)
        st.dataframe(df_inv, use_container_width=True)
        if st.button("📥 Descargar Inventario Actual (PDF)"):
            pdf_inv = exportar_inventario_pdf(df_inv)
            st.download_button(
                label="Confirmar Descarga", 
                data=pdf_inv, 
                file_name=f"stock_{date.today()}.pdf", 
                mime="application/pdf"
            )

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
    st.dataframe(df_ventas, use_container_width=True)
    
    if st.button("📥 Descargar Reporte de Ventas (PDF)"):
        if not df_ventas.empty:
            pdf_ventas = exportar_ventas_pdf(df_ventas, f_inicio, f_fin)
            st.download_button(
                label="Confirmar Descarga Reporte", 
                data=pdf_ventas, 
                file_name=f"ventas_{f_inicio}_{f_fin}.pdf", 
                mime="application/pdf"
            )

    # 4. Análisis Visual

# 4. DASHBOARD VISUAL DE RENDIMIENTO
    if not df_ventas.empty:
        st.markdown("---")
        st.subheader("📊 Análisis Visual de Ventas")

        # Preparación de datos
        df_ventas['Fecha'] = df_ventas['Fecha'].str[:10]
        
        # Fila 1: Tendencia Temporal e Ingresos por Cliente
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown("##### 📈 Tendencia de Ingresos (Bs)")
            # Agrupamos por fecha para sumar ventas del mismo día
            ventas_diarias = df_ventas.groupby('Fecha')['Total'].sum()
            st.line_chart(ventas_diarias)
            
        with col_der:
            st.markdown("##### 🏆 Top Clientes (Por Compra)")
            # Quién ha gastado más en el periodo
            top_clientes = df_ventas.groupby('Cliente')['Total'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_clientes)

        # Fila 2: Análisis de Productos
        st.markdown("---")
        col_prod1, col_prod2 = st.columns([2, 1])
        
        with col_prod1:
            st.markdown("##### 🧦 Volumen de Ventas por Producto (Unidades)")
            # Qué productos rotan más
            productos_populares = df_ventas.groupby('Producto')['Cant'].sum().sort_values(ascending=True)
            st.bar_chart(productos_populares, horizontal=True) # Gráfico horizontal para leer mejor los nombres
            
        with col_prod2:
            st.markdown("##### 💎 Resumen de Cantidades")
            # Una tabla comparativa rápida
            resumen_tabla = df_ventas.groupby('Producto').agg({
                'Cant': 'sum',
                'Total': 'sum'
            }).rename(columns={'Cant': 'Unidades', 'Total': 'Monto (Bs)'})
            st.dataframe(resumen_tabla, use_container_width=True)

    else:
        st.info("💡 No hay datos suficientes para generar gráficos en este periodo.")


