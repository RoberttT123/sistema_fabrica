import streamlit as st
import pandas as pd
import time
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
from fpdf import FPDF
import os
import io

# --- CLASE PARA EL FORMATO DEL PDF ---
class ProduccionPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Helvetica", 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'SISTEMA DE CONTROL DE PRODUCCION', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_universal(fecha, df, titulo_reporte="REPORTE"):
    """Genera un archivo PDF compatible con entornos locales y nube."""
    pdf = ProduccionPDF()
    pdf.add_page()
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"{titulo_reporte}: {fecha}", 1, 1, 'C', True)
    pdf.ln(5)

    # Configuración de tabla dinámica
    pdf.set_fill_color(144, 238, 144) 
    pdf.set_font("Helvetica", 'B', 10)
    cols = df.columns.tolist()
    
    # Calcular anchos de columna dinámicamente o fijos
    # Para mantenimiento usaremos anchos específicos si hay muchas columnas
    ancho_celda = 190 / len(cols)
    
    for col in cols:
        pdf.cell(ancho_celda, 10, str(col), 1, 0, 'C', True)
    pdf.ln()

    # Celdas de datos
    pdf.set_font("Helvetica", '', 8) # Letra más pequeña para que quepa el detalle
    for _, row in df.iterrows():
        for col in cols:
            # Multi-line cell para el campo Detalle si es necesario
            texto = str(row[col])
            pdf.cell(ancho_celda, 8, texto[:25], 1, 0, 'L') # Truncamos a 25 caracteres para mantener formato tabla
        pdf.ln()

    if 'DOCENAS' in df.columns:
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(190, 10, f"TOTAL GENERAL: {df['DOCENAS'].sum():.1f} DOCENAS", 0, 1, 'R')

    resultado = pdf.output(dest='S')
    if isinstance(resultado, (bytes, bytearray)):
        return bytes(resultado)
    return resultado.encode('latin-1', errors='replace')

def render_medias_crudo():
    st.header("🧦 Gestión de Producción y Mantenimiento")
    
    tab_dia, tab_mes, tab_mant = st.tabs([
        "📅 Registro Diario", 
        "📊 Reporte Mensual", 
        "🛠️ Mantenimiento"
    ])

    items_list = ["Soporte Lycra", "Soporte Stretch", "Pantalon Lycra", "Panty Grande", "Panty Mediano", "Pantalon Stretch"]

    # --- 1. PESTAÑA: GESTIÓN DIARIA ---
    with tab_dia:
        st.subheader("📝 Nuevo Registro de Planchado")
        with st.form("form_planchado", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1: f_reg = st.date_input("Fecha:", datetime.now())
            with c2: n_maq = st.number_input("# MAQ", min_value=1, step=1)
            with c3: it = st.selectbox("ITEM", items_list)
            with c4: part = st.number_input("# PARTIDAS", min_value=1, step=1)
            doc = st.number_input("DOCENAS", min_value=0.1, step=0.5, format="%.1f")
            
            if st.form_submit_button("📥 Guardar Producción", use_container_width=True):
                ejecutar_consulta("INSERT INTO produccion_crudo (fecha, n_maquina, item, n_partidas, docenas) VALUES (?, ?, ?, ?, ?)", (f_reg.strftime('%Y-%m-%d'), n_maq, it, part, doc))
                st.success("✅ Registro guardado"); time.sleep(1); st.rerun()

        st.divider()
        f_busq = st.date_input("Consultar fecha:", datetime.now(), key="f_diaria")
        df_dia = obtener_datos("SELECT id as ID, n_maquina as '# MAQ', item as ITEM, n_partidas as '# PART', docenas as DOCENAS FROM produccion_crudo WHERE fecha = ?", (f_busq.strftime('%Y-%m-%d'),))
        
        if not df_dia.empty:
            st.dataframe(df_dia, use_container_width=True, hide_index=True)
            c_p, c_e = st.columns(2)
            with c_p:
                pdf_d = generar_pdf_universal(f_busq.strftime('%d/%m/%Y'), df_dia, "PRODUCCION DIARIA")
                st.download_button("📄 PDF Diario", data=pdf_d, file_name=f"Reporte_{f_busq}.pdf", use_container_width=True)
            with c_e:
                out = io.BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df_dia.to_excel(writer, index=False, sheet_name='Diario')
                st.download_button("📗 Excel Diario", data=out.getvalue(), file_name=f"Reporte_{f_busq}.xlsx", use_container_width=True)

    # --- 2. PESTAÑA: REPORTE MENSUAL ---
    with tab_mes:
        st.subheader("📊 Análisis Mensual")
        col_m, col_a = st.columns(2)
        with col_m: m_sel = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 1)
        with col_a: a_sel = st.selectbox("Año", [2024, 2025, 2026], index=2)

        df_m_item = obtener_datos("SELECT item as ITEM, SUM(docenas) as DOCENAS FROM produccion_crudo WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=? GROUP BY item", (f"{m_sel:02d}", str(a_sel)))
        df_m_maq = obtener_datos("SELECT n_maquina as MAQ, SUM(docenas) as DOCENAS FROM produccion_crudo WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=? GROUP BY n_maquina ORDER BY DOCENAS DESC", (f"{m_sel:02d}", str(a_sel)))

        if not df_m_item.empty:
            total_m = df_m_item['DOCENAS'].sum()
            maq_lider = df_m_maq.iloc[0]['MAQ'] if not df_m_maq.empty else "N/A"
            st.metric("PRODUCCIÓN TOTAL", f"{total_m:.1f} DOC", help=f"Líder: Máquina #{int(maq_lider)}")

            g1, g2 = st.columns(2)
            with g1: st.bar_chart(df_m_item.set_index('ITEM'))
            with g2: st.bar_chart(df_m_maq.set_index('MAQ'), color="#ffaa00")

            pdf_m = generar_pdf_universal(f"{m_sel}/{a_sel}", df_m_item, "REPORTE MENSUAL")
            st.download_button("📄 Descargar PDF Mensual", data=pdf_m, file_name=f"Mensual_{m_sel}.pdf", use_container_width=True)

    # --- 3. PESTAÑA: MANTENIMIENTO ---
    with tab_mant:
        st.subheader("🛠️ Registro de Mantenimiento")
        with st.form("form_mant", clear_on_submit=True):
            cm1, cm2 = st.columns(2)
            with cm1:
                f_mant = st.date_input("Fecha:", datetime.now())
                n_maq_m = st.number_input("Máquina #:", min_value=1, step=1)
            with cm2:
                t_mant = st.selectbox("Tipo:", ["Preventivo", "Correctivo", "Limpieza", "Repuesto"])
                tec = st.text_input("Técnico:")
            det = st.text_area("Descripción de la reparación:")
            if st.form_submit_button("🔧 Registrar Servicio", use_container_width=True):
                ejecutar_consulta("INSERT INTO mantenimiento (fecha, n_maquina, tipo, detalle, tecnico) VALUES (?,?,?,?,?)", (f_mant.strftime('%Y-%m-%d'), n_maq_m, t_mant, det, tec))
                st.success("Servicio registrado"); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("📋 Historial y Reporte de Mantenimiento")
        
        # Selector de mes para el reporte de mantenimiento
        col_hm, col_ha = st.columns(2)
        with col_hm: m_mant = st.selectbox("Mes Historial", range(1, 13), index=datetime.now().month - 1, key="m_mant")
        with col_ha: a_mant = st.selectbox("Año Historial", [2024, 2025, 2026], index=2, key="a_mant")

        df_hist = obtener_datos("""
            SELECT fecha as Fecha, n_maquina as MAQ, tipo as Tipo, tecnico as Tecnico, detalle as Detalle 
            FROM mantenimiento 
            WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=?
            ORDER BY fecha DESC
        """, (f"{m_mant:02d}", str(a_mant)))

        if not df_hist.empty:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
            
            # Botón para descargar PDF de Mantenimiento
            pdf_mant_bytes = generar_pdf_universal(f"{m_mant}/{a_mant}", df_hist, "REPORTE DE MANTENIMIENTO")
            st.download_button(
                label="📄 Descargar PDF de Mantenimientos",
                data=pdf_mant_bytes,
                file_name=f"Mantenimiento_{m_mant}_{a_mant}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("No hay registros de mantenimiento para este periodo.")