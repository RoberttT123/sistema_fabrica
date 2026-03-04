import streamlit as st
import pandas as pd
import io
from modules.database import obtener_datos
from fpdf import FPDF
import os
from datetime import datetime, date

# --- 1. FUNCIONES DE EXPORTACIÓN (PDF) ---

def exportar_inventario_pdf(df):
    """Mantiene el reporte de inventario actual."""
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=3, w=17) 
    
    pdf.set_font("Helvetica", 'B', 14)
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
    
    return bytes(pdf.output(dest='S')) if not isinstance(pdf.output(dest='S'), str) else pdf.output(dest='S').encode('latin-1')

def exportar_ventas_mensuales_pdf(df, mes_nombre, anio):
    """Reporte de ventas con el orden: FECHA, CIUDAD, CLIENTE, CANT, PRESENTACION, MATERIAL, P.UNIT, TOTAL."""
    pdf = FPDF(orientation='L', unit='mm', format='A4') # Orientación horizontal para que quepan las columnas
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=10, y=8, w=20) 
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, txt=f"REPORTE DE VENTAS - {mes_nombre.upper()} {anio}", ln=True, align='C')
    pdf.ln(5)
    
    # Encabezados ajustados (Ancho total A4 horizontal aprox 277mm)
    # FECHA(25), CIUDAD(30), CLIENTE(45), CANT(20), PRESENTACION(45), MATERIAL(40), P.UNIT(30), TOTAL(30)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(25, 10, "FECHA", 1, 0, 'C', True)
    pdf.cell(30, 10, "CIUDAD", 1, 0, 'C', True)
    pdf.cell(45, 10, "CLIENTE", 1, 0, 'C', True)
    pdf.cell(20, 10, "CANT.", 1, 0, 'C', True)
    pdf.cell(45, 10, "PRESENTACION", 1, 0, 'C', True)
    pdf.cell(40, 10, "MATERIAL", 1, 0, 'C', True)
    pdf.cell(30, 10, "P. UNIT", 1, 0, 'C', True)
    pdf.cell(30, 10, "TOTAL Bs", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        cant = float(row['Cant'] or 1)
        total = float(row['Total'] or 0)
        p_unit = total / cant if cant > 0 else 0
        
        pdf.cell(25, 9, pd.to_datetime(row['Fecha']).strftime('%d/%m/%Y'), 1, 0, 'C')
        pdf.cell(30, 9, str(row['Ciudad'])[:15], 1)
        pdf.cell(45, 9, str(row['Cliente'])[:22], 1)
        pdf.cell(20, 9, str(row['Cant']), 1, 0, 'C')
        pdf.cell(45, 9, str(row['Presentacion'])[:22], 1)
        pdf.cell(40, 9, str(row['Material'])[:18], 1)
        pdf.cell(30, 9, f"{p_unit:.2f}", 1, 0, 'R')
        pdf.cell(30, 9, f"{total:.2f}", 1, 1, 'R')
    
    pdf.ln(2)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    # Sumar anchos anteriores hasta P.UNIT = 235
    pdf.cell(235, 10, f"TOTAL ACUMULADO {mes_nombre.upper()}:", 1, 0, 'R', True)
    pdf.cell(30, 10, f"{df['Total'].sum():.2f} Bs", 1, 1, 'C', True)
        
    return bytes(pdf.output(dest='S')) if not isinstance(pdf.output(dest='S'), str) else pdf.output(dest='S').encode('latin-1')

# --- 2. FUNCIÓN DE EXPORTACIÓN (EXCEL) ---

def generar_excel_mensual(df, mes_nombre):
    """Genera Excel con el orden de columnas solicitado."""
    output = io.BytesIO()
    df_excel = df.copy()
    
    # Calcular Precio Unitario
    df_excel['PRECIO UNITARIO'] = (df_excel['Total'] / df_excel['Cant']).round(2)
    df_excel['FECHA'] = pd.to_datetime(df_excel['Fecha']).dt.strftime('%d/%m/%Y')
    
    # Renombrar y Reordenar
    df_excel = df_excel.rename(columns={
        'Ciudad': 'CIUDAD',
        'Cliente': 'CLIENTE',
        'Cant': 'CANT. DOC',
        'Presentacion': 'PRESENTACION',
        'Material': 'MATERIAL',
        'Total': 'TOTAL'
    })
    
    columnas_orden = ['FECHA', 'CIUDAD', 'CLIENTE', 'CANT. DOC', 'PRESENTACION', 'MATERIAL', 'PRECIO UNITARIO', 'TOTAL']
    df_excel = df_excel[columnas_orden]
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name=f'Ventas_{mes_nombre}')
    return output.getvalue()

# --- 3. FUNCIÓN PRINCIPAL DE RENDERIZADO ---

def render_reportes():
    st.header("📊 Dashboard de Gestión y Ventas")

    # --- KPI'S RESUMEN EJECUTIVO ---
    st.sidebar.subheader("📅 Rango Global")
    f_inicio = st.sidebar.date_input("Desde", date.today().replace(day=1))
    f_fin = st.sidebar.date_input("Hasta", date.today())

    st.subheader(f"📈 Resumen: {f_inicio.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')}")
    
    v_data = obtener_datos("SELECT SUM(precio) as total FROM pedidos WHERE fecha::date BETWEEN %s AND %s", (f_inicio, f_fin))
    ventas_periodo = float(v_data.iloc[0]['total'] or 0)
    cli_data = obtener_datos("SELECT COUNT(*) as total FROM clientes")
    stock_data = obtener_datos("SELECT COUNT(*) as total FROM inventario WHERE cantidad < 10")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Ventas Periodo", f"{ventas_periodo:.2f} Bs")
    m2.metric("👥 Total Clientes", int(cli_data.iloc[0]['total'] or 0))
    m3.metric("⚠️ Stock Crítico", int(stock_data.iloc[0]['total'] or 0))
    
    # --- INVENTARIO ---
    st.markdown("---")
    with st.expander("📦 Consultar Inventario Actual"):
        df_inv = obtener_datos('SELECT id as "ID", linea as "Línea", tamano as "Tipo", color as "Color", cantidad as "Cantidad", precio_venta as "Precio" FROM inventario ORDER BY cantidad ASC')
        if not df_inv.empty:
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
            if st.button("📄 Exportar Inventario PDF"):
                st.download_button("📥 Descargar PDF", exportar_inventario_pdf(df_inv), f"inventario_{date.today()}.pdf")

    # --- ANÁLISIS MENSUAL ---
    st.markdown("---")
    st.subheader("💰 Historial de Ventas Mensuales")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        mes_nombre = st.selectbox("Seleccione el Mes", meses, index=datetime.now().month - 1)
        mes_idx = meses.index(mes_nombre) + 1
    with c_m2:
        anio_sel = st.selectbox("Año", [2024, 2025, 2026], index=datetime.now().year - 2024)

    # CONSULTA MODIFICADA: Ahora trae 'nombre' como Presentación y 'linea' como Material
    query_ventas = """
        SELECT 
            p.fecha as "Fecha",
            d.nombre as "Ciudad",
            COALESCE(c.nombre, 'Venta Directa') as "Cliente", 
            p.cantidad as "Cant",
            i.nombre as "Presentacion",
            i.linea as "Material",
            p.precio as "Total"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN departamentos d ON c.id_depto = d.id_depto
        LEFT JOIN inventario i ON p.id_inventario = i.id
        WHERE EXTRACT(MONTH FROM p.fecha) = %s AND EXTRACT(YEAR FROM p.fecha) = %s
        ORDER BY p.fecha ASC
    """
    df_ventas = obtener_datos(query_ventas, (mes_idx, anio_sel))
    
    if not df_ventas.empty:
        # --- TABLA Y DESCARGAS ---
        st.write(f"#### 📋 Movimientos de {mes_nombre} {anio_sel}")
        df_display = df_ventas.copy()
        df_display['P. Unit'] = (df_display['Total'] / df_display['Cant']).round(2)
        df_display['Fecha'] = pd.to_datetime(df_display['Fecha']).dt.strftime('%d/%m/%Y')
        
        # Orden de columnas para la pantalla
        cols_vista = ['Fecha', 'Ciudad', 'Cliente', 'Cant', 'Presentacion', 'Material', 'P. Unit', 'Total']
        st.dataframe(df_display[cols_vista], use_container_width=True, hide_index=True)
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button(f"📄 Descargar PDF {mes_nombre}"):
                pdf_bytes = exportar_ventas_mensuales_pdf(df_ventas, mes_nombre, anio_sel)
                st.download_button("📥 Confirmar PDF", pdf_bytes, f"Ventas_{mes_nombre}.pdf", "application/pdf")
        
        with c_btn2:
            excel_bytes = generar_excel_mensual(df_ventas, mes_nombre)
            st.download_button(
                label=f"📗 Descargar Excel {mes_nombre}",
                data=excel_bytes,
                file_name=f"Reporte_Ventas_{mes_nombre}_{anio_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info(f"No se encontraron registros en {mes_nombre} {anio_sel}.")