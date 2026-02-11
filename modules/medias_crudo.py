import streamlit as st
import pandas as pd
import time
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
from fpdf import FPDF
import os

class ProduccionPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Arial", 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'REPORTE DE PRODUCCIÓN EN CRUDO', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_produccion(fecha, df):
    pdf = ProduccionPDF()
    pdf.add_page()
    
    # --- ENCABEZADO DE FECHA ---
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"FECHA DEL REPORTE: {fecha}", 1, 1, 'C', True)
    pdf.ln(5)

    # --- TABLA 1: DETALLE POR MÁQUINA ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "DETALLE DE PLANCHADO POR MÁQUINA", 0, 1, 'L')
    
    pdf.set_fill_color(144, 238, 144) # Verde
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, "# MAQ", 1, 0, 'C', True)
    pdf.cell(70, 10, "ITEM", 1, 0, 'C', True)
    pdf.cell(40, 10, "# PARTIDAS", 1, 0, 'C', True)
    pdf.cell(50, 10, "DOCENAS", 1, 1, 'C', True)

    pdf.set_font("Arial", '', 10)
    for _, row in df.iterrows():
        pdf.cell(30, 8, str(row['# MAQ']), 1, 0, 'C')
        pdf.cell(70, 8, str(row['ITEM']), 1, 0, 'L')
        pdf.cell(40, 8, str(row['# PARTIDAS']), 1, 0, 'C')
        pdf.cell(50, 8, f"{row['DOCENAS']:.1f}", 1, 1, 'R')

    pdf.ln(10)

    # --- TABLA 2: RESUMEN TOTAL POR ITEM (NUEVA SECCIÓN) ---
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "RESUMEN TOTAL POR TIPO DE ITEM", 0, 1, 'L')
    
    # Agrupar datos por ITEM
    resumen_items = df.groupby('ITEM')['DOCENAS'].sum().reset_index()
    
    pdf.set_fill_color(255, 215, 0) # Dorado/Amarillo para resaltar
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 10, "ITEM / PRODUCTO", 1, 0, 'C', True)
    pdf.cell(90, 10, "TOTAL DOCENAS", 1, 1, 'C', True)

    pdf.set_font("Arial", '', 10)
    for _, row in resumen_items.iterrows():
        pdf.cell(100, 8, str(row['ITEM']), 1, 0, 'L')
        pdf.cell(90, 8, f"{row['DOCENAS']:.1f}", 1, 1, 'R')

    # --- TOTAL GENERAL ---
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(100, 10, "TOTAL GENERAL DEL DÍA:", 1, 0, 'R', True)
    pdf.cell(90, 10, f"{df['DOCENAS'].sum():.1f} DOCENAS", 1, 1, 'C', True)

    return pdf.output(dest='S').encode('latin-1', errors='replace')

def render_medias_crudo():
    st.header("🧦 Producción: Planchado en Crudo")

    items_list = ["Soporte Lycra", "Soporte Stretch", "Pantalon Lycra", "Panty Grande", "Panty Mediano", "Pantalon Stretch"]

    # --- 1. FORMULARIO DE REGISTRO ---
    with st.form("form_planchado", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fecha_sel = st.date_input("Fecha:", datetime.now())
        with col2:
            n_maquina = st.number_input("# MAQ", min_value=1, step=1)
        with col3:
            item = st.selectbox("ITEM", items_list)
        with col4:
            n_partidas = st.number_input("# PARTIDAS", min_value=1, step=1)

        docenas = st.number_input("DOCENAS", min_value=0.1, step=0.5, format="%.1f")
        
        if st.form_submit_button("📥 Registrar Planchado", use_container_width=True):
            query = "INSERT INTO produccion_crudo (fecha, n_maquina, item, n_partidas, docenas) VALUES (?, ?, ?, ?, ?)"
            ejecutar_consulta(query, (fecha_sel.strftime('%Y-%m-%d'), n_maquina, item, n_partidas, docenas))
            st.success("✅ Registro guardado")
            time.sleep(1)
            st.rerun()

    st.divider()

    # --- 2. RESUMEN, PDF Y EDICIÓN ---
    st.subheader(f"📊 Resumen de Planchado - {fecha_sel.strftime('%d/%m/%Y')}")
    
    query_ver = "SELECT id as ID, n_maquina as '# MAQ', item as 'ITEM', n_partidas as '# PARTIDAS', docenas as 'DOCENAS' FROM produccion_crudo WHERE fecha = ?"
    df_crudo = obtener_datos(query_ver, (fecha_sel.strftime('%Y-%m-%d'),))

    if not df_crudo.empty:
        st.dataframe(df_crudo, use_container_width=True, hide_index=True)
        
        # Generar y descargar PDF
        pdf_data = generar_pdf_produccion(fecha_sel.strftime('%d/%m/%Y'), df_crudo)
        st.download_button(
            label="📄 Descargar PDF Reporte Completo",
            data=pdf_data,
            file_name=f"Reporte_Produccion_{fecha_sel}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        # SECCIÓN DE EDICIÓN / ELIMINACIÓN
        col_e, col_d = st.columns(2)
        with col_e:
            with st.expander("📝 Editar Registro"):
                id_edit = st.number_input("ID a editar:", min_value=1, step=1, key="ed_crudo")
                reg_actual = df_crudo[df_crudo['ID'] == id_edit]
                if not reg_actual.empty:
                    with st.form("edit_crudo"):
                        m = st.number_input("# MAQ", value=int(reg_actual.iloc[0]['# MAQ']))
                        idx = items_list.index(reg_actual.iloc[0]['ITEM']) if reg_actual.iloc[0]['ITEM'] in items_list else 0
                        it = st.selectbox("ITEM", items_list, index=idx)
                        p = st.number_input("# PARTIDAS", value=int(reg_actual.iloc[0]['# PARTIDAS']))
                        d = st.number_input("DOCENAS", value=float(reg_actual.iloc[0]['DOCENAS']), step=0.5)
                        if st.form_submit_button("Guardar Cambios"):
                            ejecutar_consulta("UPDATE produccion_crudo SET n_maquina=?, item=?, n_partidas=?, docenas=? WHERE id=?", (m, it, p, d, id_edit))
                            st.rerun()
        with col_d:
            with st.expander("🗑️ Eliminar"):
                id_del = st.number_input("ID a eliminar:", min_value=1, step=1, key="del_crudo")
                if st.button("Confirmar Borrado", type="primary"):
                    ejecutar_consulta("DELETE FROM produccion_crudo WHERE id=?", (id_del,))
                    st.rerun()
    else:
        st.info("No hay registros para esta fecha.")