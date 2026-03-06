import streamlit as st
import pandas as pd
import io
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

# --- 1. LÓGICA DE NEGOCIO (CLASIFICACIÓN) ---

def obtener_clase(total):
    """A >= 5000, B entre 3000 y 5000, C < 3000"""
    total_val = float(total or 0)
    if total_val >= 5000:
        return "A"
    elif 3000 <= total_val < 5000:
        return "B"
    else:
        return "C"

def obtener_tipo_cliente(clase):
    """Mapeo de Tipo para el Excel: A=Distribuidor, B=Minorista, C=Usuario Final"""
    mapping = {"A": "Distribuidor", "B": "Minorista", "C": "Usuario Final"}
    return mapping.get(clase, "Final")

# --- 2. FUNCIONES DE EXPORTACIÓN (PDF) ---

def exportar_inventario_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=22) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.ln(4) # Espacio vertical para separar el título del logo
    pdf.cell(200, 10, txt="REPORTE DE INVENTARIO - FABRICA DE MEDIAS", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    headers = [("ID", 15), ("Linea", 35), ("Tipo", 50), ("Color", 35), ("Stock", 25), ("Precio", 30)]
    for txt, w in headers:
        pdf.cell(w, 10, txt, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        pdf.cell(15, 10, str(row['ID']), 1)
        pdf.cell(35, 10, str(row['Línea']), 1)
        pdf.cell(50, 10, str(row['Tipo'])[:25], 1)
        pdf.cell(35, 10, str(row['Color']), 1)
        pdf.cell(25, 10, str(row['Cantidad']), 1)
        pdf.cell(30, 10, f"{float(row['Precio'] or 0):.2f} Bs", 1, 1)
    
    salida = pdf.output(dest='S')
    return bytes(salida) if isinstance(salida, (bytearray, bytes)) else salida.encode('latin-1')

def exportar_ventas_mensuales_pdf(df, mes_nombre, anio):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=22) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.ln(4) # Espacio vertical para separar el título del logo
    pdf.cell(0, 10, txt=f"REPORTE DE VENTAS Y CLASIFICACION - {mes_nombre.upper()} {anio}", ln=True, align='C')
    pdf.ln(5)
    
    # Tabla 1: Detalle de Ventas
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    headers = [("FECHA", 25), ("CIUDAD", 30), ("CLIENTE", 45), ("CANT.", 20), ("PRESENTACION", 45), ("MATERIAL", 40), ("P. UNIT", 30), ("TOTAL Bs", 30)]
    for txt, w in headers:
        pdf.cell(w, 10, txt, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        cant = float(row['Cant'] or 1)
        total = float(row['Total'] or 0)
        p_unit = total / cant if cant > 0 else 0
        pdf.cell(25, 8, pd.to_datetime(row['Fecha']).strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(30, 8, str(row['Ciudad'])[:15], 1)
        pdf.cell(45, 8, str(row['Cliente'])[:22], 1)
        pdf.cell(20, 8, str(row['Cant']), 1, 0, 'C')
        pdf.cell(45, 8, str(row['Presentacion'])[:22], 1)
        pdf.cell(40, 8, str(row['Material'])[:18], 1)
        pdf.cell(30, 8, f"{p_unit:.2f}", 1, 0, 'R')
        pdf.cell(30, 8, f"{total:.2f}", 1, 1, 'R')
    
    # Total Final
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(235, 10, f"TOTAL ACUMULADO {mes_nombre.upper()}:", 1, 0, 'R', True)
    pdf.cell(30, 10, f"{df['Total'].sum():.2f} Bs", 1, 1, 'C', True)
    
    # Tabla 2: Clasificación (Resumen PDF)
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "RESUMEN DE CLASIFICACION DE CLIENTES", ln=True)
    pdf.ln(2)
    
    df_rank = df.groupby('Cliente')['Total'].sum().reset_index()
    df_rank['Clase'] = df_rank['Total'].apply(obtener_clase)
    df_rank = df_rank.sort_values(by='Total', ascending=False)
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 10, "NOMBRE DEL CLIENTE", 1, 0, 'C', True)
    pdf.cell(40, 10, "CLASIFICACION", 1, 0, 'C', True)
    pdf.cell(50, 10, "TOTAL MES (Bs)", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=10)
    for _, row in df_rank.iterrows():
        pdf.cell(100, 9, str(row['Cliente']), 1)
        clase = row['Clase']
        if clase == 'A': pdf.set_text_color(0, 128, 0)
        elif clase == 'B': pdf.set_text_color(255, 140, 0)
        else: pdf.set_text_color(200, 0, 0)
        pdf.cell(40, 9, f"CLASE {clase}", 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 9, f"{row['Total']:.2f}", 1, 1, 'R')
        
    salida = pdf.output(dest='S')
    return bytes(salida) if isinstance(salida, (bytearray, bytes)) else salida.encode('latin-1')

# --- 3. FUNCIÓN DE EXPORTACIÓN (EXCEL) ---

def generar_excel_mensual(df, mes_nombre):
    output = io.BytesIO()
    
    # Hoja 1: Detalle Ventas
    df_v = df.copy()
    df_v['PRECIO UNITARIO'] = (df_v['Total'] / df_v['Cant']).round(2)
    df_v['FECHA'] = pd.to_datetime(df_v['Fecha']).dt.strftime('%d/%m/%Y')
    df_v = df_v.rename(columns={'Ciudad':'CIUDAD','Cliente':'CLIENTE','Cant':'CANT. DOC','Presentacion':'PRESENTACION','Material':'MATERIAL','Total':'TOTAL'})
    cols_v = ['FECHA', 'CIUDAD', 'CLIENTE', 'CANT. DOC', 'PRESENTACION', 'MATERIAL', 'PRECIO UNITARIO', 'TOTAL']
    
    # Hoja 2: Clasificación ABC (Orden solicitado)
    df_abc = df.groupby('Cliente').agg({
        'Total': 'sum',
        'Ciudad': 'first',
        'Telefono': 'first',
        'Direccion': 'first'
    }).reset_index()
    
    df_abc['CLASE'] = df_abc['Total'].apply(obtener_clase)
    df_abc['TIPO'] = df_abc['CLASE'].apply(obtener_tipo_cliente)
    
    df_abc = df_abc.rename(columns={'Cliente': 'NOMBRE CLIENTE', 'Ciudad': 'DEPARTAMENTO', 'Telefono': 'TELEFONO', 'Direccion': 'DIRECCION'})
    
    # Reordenar: NOMBRE CLIENTE - CLASE - TELEFONO - TIPO - DEPARTAMENTO - DIRECCION
    cols_abc = ['NOMBRE CLIENTE', 'CLASE', 'TELEFONO', 'TIPO', 'DEPARTAMENTO', 'DIRECCION']
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v[cols_v].to_excel(writer, index=False, sheet_name='Detalle Ventas')
        df_abc[cols_abc].to_excel(writer, index=False, sheet_name='Clasificacion ABC')
    return output.getvalue()

# --- 4. FUNCIÓN PRINCIPAL DE RENDERIZADO ---

def render_reportes():
    st.header("📊 Dashboard de Gestión y Ventas")

    # --- KPI'S ---
    st.sidebar.subheader("📅 Rango Global")
    f_inicio = st.sidebar.date_input("Desde", date.today().replace(day=1))
    f_fin = st.sidebar.date_input("Hasta", date.today())
    
    v_data = obtener_datos("SELECT SUM(precio) as total FROM pedidos WHERE fecha::date BETWEEN %s AND %s", (f_inicio, f_fin))
    ventas_periodo = float(v_data.iloc[0]['total'] or 0)
    cli_data = obtener_datos("SELECT COUNT(*) as total FROM clientes")
    stock_data = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Ventas Periodo", f"{ventas_periodo:.2f} Bs")
    m2.metric("👥 Total Clientes", int(cli_data.iloc[0]['total'] or 0))
    m3.metric("⚠️ Stock Crítico", int(stock_data.iloc[0]['total'] or 0))
    
    # --- SECCIÓN INVENTARIO ---
    st.markdown("---")
    with st.expander("📦 Consultar Inventario Actual"):
        df_inv = obtener_datos('SELECT id as "ID", linea as "Línea", tamano as "Tipo", color as "Color", cantidad as "Cantidad", precio_venta as "Precio" FROM inventario ORDER BY cantidad ASC')
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
            st.download_button("📥 Descargar Inventario", exportar_inventario_pdf(df_inv), f"inventario_{date.today()}.pdf")

    # --- ANÁLISIS MENSUAL ---
    st.markdown("---")
    st.subheader("💰 Historial de Ventas y Clasificación")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_nombre = st.selectbox("Seleccione el Mes", meses, index=datetime.now().month - 1)
        mes_idx = meses.index(mes_nombre) + 1
    with c_m2:
        anio_sel = st.selectbox("Año", [2024, 2025, 2026], index=datetime.now().year - 2024)

    # Consulta SQL con Teléfono y Dirección
    query_ventas = """
        SELECT p.fecha as "Fecha", d.nombre as "Ciudad", COALESCE(c.nombre, 'Venta Directa') as "Cliente", 
               c.telefono as "Telefono", c.direccion as "Direccion",
               p.cantidad as "Cant", i.nombre as "Presentacion", i.linea as "Material", p.precio as "Total"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN departamentos d ON c.id_depto = d.id_depto
        LEFT JOIN inventario i ON p.id_inventario = i.id
        WHERE EXTRACT(MONTH FROM p.fecha) = %s AND EXTRACT(YEAR FROM p.fecha) = %s
        ORDER BY p.fecha ASC
    """
    df_ventas = obtener_datos(query_ventas, (mes_idx, anio_sel))
    
    if not df_ventas.empty:
        st.write(f"#### 📋 Movimientos de {mes_nombre} {anio_sel}")
        
        # --- AJUSTES DE VISUALIZACIÓN EN PANTALLA ---
        df_display = df_ventas.copy()
        
        # 1. Ajuste de Fecha (quitar hora y zona horaria)
        df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
        
        # 2. Ajuste de Precios y Totales con 'Bs' y 2 decimales
        df_display['P. Unit'] = (df_display['Total'] / df_display['Cant']).apply(lambda x: f"{x:.2f} Bs")
        df_display['Total'] = df_display['Total'].apply(lambda x: f"{x:.2f} Bs")
        
        # Ocultamos teléfono y dirección en la pantalla
        st.dataframe(df_display.drop(columns=['Telefono', 'Direccion']), use_container_width=True, hide_index=True)

        st.markdown("### 🏆 Clasificación de Clientes del Mes")
        df_ranking = df_ventas.groupby('Cliente')['Total'].sum().reset_index()
        df_ranking['Clase'] = df_ranking['Total'].apply(obtener_clase)
        df_ranking = df_ranking.sort_values(by='Total', ascending=False)
        
        # 3. Ajuste de Total en la tabla de Clasificación con 'Bs'
        df_ranking_vista = df_ranking.copy()
        df_ranking_vista['Total'] = df_ranking_vista['Total'].apply(lambda x: f"{x:.2f} Bs")
        
        col_cl1, col_cl2 = st.columns([2, 1])
        with col_cl1:
            st.table(df_ranking_vista)
        with col_cl2:
            st.info(f"**Resumen Mensual:**\n- Clase A: {len(df_ranking[df_ranking['Clase']=='A'])}\n- Clase B: {len(df_ranking[df_ranking['Clase']=='B'])}\n- Clase C: {len(df_ranking[df_ranking['Clase']=='C'])}")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            st.download_button("📥 Descargar Reporte PDF", exportar_ventas_mensuales_pdf(df_ventas, mes_nombre, anio_sel), f"Reporte_{mes_nombre}.pdf")
        with c_btn2:
            st.download_button("📗 Descargar Excel ", generar_excel_mensual(df_ventas, mes_nombre), f"Ventas_{mes_nombre}_{anio_sel}.xlsx")
    else:
        st.info("No hay datos para este mes.")