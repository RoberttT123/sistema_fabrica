import streamlit as st
import pandas as pd
import time
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
from fpdf import FPDF
import os

# --- CLASE PARA EL FORMATO DEL PDF ---
class ProduccionPDF(FPDF):
    def header(self):
        # Logo opcional
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        # Usamos Helvetica por ser estándar en Linux/Nube y Mac
        self.set_font("Helvetica", 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'REPORTE DE PRODUCCION EN CRUDO', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_produccion(fecha, df):
    pdf = ProduccionPDF()
    pdf.add_page()
    
    # --- ENCABEZADO DE FECHA ---
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"FECHA DEL REPORTE: {fecha}", 1, 1, 'C', True)
    pdf.ln(5)

    # --- TABLA 1: DETALLE POR MAQUINA ---
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "DETALLE DE PLANCHADO POR MAQUINA", 0, 1, 'L')
    
    pdf.set_fill_color(144, 238, 144) # Verde
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(30, 10, "# MAQ", 1, 0, 'C', True)
    pdf.cell(70, 10, "ITEM", 1, 0, 'C', True)
    pdf.cell(40, 10, "# PARTIDAS", 1, 0, 'C', True)
    pdf.cell(50, 10, "DOCENAS", 1, 1, 'C', True)

    pdf.set_font("Helvetica", '', 10)
    for _, row in df.iterrows():
        pdf.cell(30, 8, str(row['# MAQ']), 1, 0, 'C')
        pdf.cell(70, 8, str(row['ITEM']), 1, 0, 'L')
        pdf.cell(40, 8, str(row['# PARTIDAS']), 1, 0, 'C')
        pdf.cell(50, 8, f"{row['DOCENAS']:.1f}", 1, 1, 'R')

    pdf.ln(10)

    # --- TABLA 2: RESUMEN TOTAL POR ITEM ---
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(0, 10, "RESUMEN TOTAL POR TIPO DE ITEM", 0, 1, 'L')
    
    resumen_items = df.groupby('ITEM')['DOCENAS'].sum().reset_index()
    
    pdf.set_fill_color(255, 215, 0) # Dorado
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(100, 10, "ITEM / PRODUCTO", 1, 0, 'C', True)
    pdf.cell(90, 10, "TOTAL DOCENAS", 1, 1, 'C', True)

    pdf.set_font("Helvetica", '', 10)
    for _, row in resumen_items.iterrows():
        pdf.cell(100, 8, str(row['ITEM']), 1, 0, 'L')
        pdf.cell(90, 8, f"{row['DOCENAS']:.1f}", 1, 1, 'R')

    # --- TOTAL GENERAL ---
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(100, 10, "TOTAL GENERAL DEL DIA:", 1, 0, 'R', True)
    pdf.cell(90, 10, f"{df['DOCENAS'].sum():.1f} DOCENAS", 1, 1, 'C', True)

    # --- SOLUCION UNIVERSAL PARA LOCAL Y NUBE ---
    resultado = pdf.output(dest='S')
    if isinstance(resultado, (bytes, bytearray)):
        return bytes(resultado)
    return resultado.encode('latin-1', errors='replace')

def render_medias_crudo():
    st.header("🧦 Producción: Planchado en Crudo")
    
    items_list = [
        "Soporte Lycra", "Soporte Stretch", "Pantalon Lycra", 
        "Panty Grande", "Panty Mediano", "Pantalon Stretch"
    ]

    # --- 1. FORMULARIO DE REGISTRO ---
    st.subheader("📝 Nuevo Registro")
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

    # --- 2. RESUMEN Y ACCIONES ---
    st.subheader(f"📊 Resumen de Planchado - {fecha_sel.strftime('%d/%m/%Y')}")
    
    query_ver = "SELECT id as ID, n_maquina as '# MAQ', item as 'ITEM', n_partidas as '# PARTIDAS', docenas as 'DOCENAS' FROM produccion_crudo WHERE fecha = ?"
    df_crudo = obtener_datos(query_ver, (fecha_sel.strftime('%Y-%m-%d'),))

    if not df_crudo.empty:
        st.dataframe(df_crudo, use_container_width=True, hide_index=True)
        
        # Botón PDF
        try:
            pdf_bytes = generar_pdf_produccion(fecha_sel.strftime('%d/%m/%Y'), df_crudo)
            st.download_button(
                label="📄 Descargar PDF Reporte Completo",
                data=pdf_bytes,
                file_name=f"Reporte_Produccion_{fecha_sel}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar el PDF: {e}")

        # --- SECCIÓN DE EDICIÓN Y ELIMINACIÓN ---
        col_e, col_d = st.columns(2)
        
        with col_e:
            with st.expander("📝 Editar Registro"):
                id_edit = st.number_input("ID a editar:", min_value=1, step=1, key="ed_crudo_btn")
                reg_actual = df_crudo[df_crudo['ID'] == id_edit]
                
                if not reg_actual.empty:
                    with st.form("form_edit_actual"):
                        m = st.number_input("# MAQ", value=int(reg_actual.iloc[0]['# MAQ']))
                        idx_item = items_list.index(reg_actual.iloc[0]['ITEM']) if reg_actual.iloc[0]['ITEM'] in items_list else 0
                        it = st.selectbox("ITEM", items_list, index=idx_item)
                        p = st.number_input("# PARTIDAS", value=int(reg_actual.iloc[0]['# PARTIDAS']))
                        d = st.number_input("DOCENAS", value=float(reg_actual.iloc[0]['DOCENAS']), step=0.1)
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            q_upd = "UPDATE produccion_crudo SET n_maquina=?, item=?, n_partidas=?, docenas=? WHERE id=?"
                            ejecutar_consulta(q_upd, (m, it, p, d, id_edit))
                            st.success("Actualizado"); time.sleep(1); st.rerun()
                else:
                    st.caption("Seleccione un ID de la tabla.")

        with col_d:
            with st.expander("🗑️ Eliminar"):
                id_del = st.number_input("ID a eliminar:", min_value=1, step=1, key="del_crudo_btn")
                if st.button("Confirmar Borrado", type="primary", use_container_width=True):
                    ejecutar_consulta("DELETE FROM produccion_crudo WHERE id=?", (id_del,))
                    st.warning(f"ID {id_del} eliminado"); time.sleep(1); st.rerun()
    else:
        st.info("No hay registros para esta fecha.")