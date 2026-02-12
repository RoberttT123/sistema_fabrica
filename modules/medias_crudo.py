import streamlit as st
import pandas as pd
import time
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
from fpdf import FPDF
import os
import io
import urllib.parse

# --- CONFIGURACIÓN ---
TELEFONO_DESTINO = "59178790265" 

# --- CLASE PARA EL FORMATO DEL PDF ---
class ProduccionPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Helvetica", 'B', 15)
        self.cell(0, 10, 'SISTEMA DE CONTROL DE PRODUCCION Y MANTENIMIENTO', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- FUNCIONES DE SOPORTE ---
def generar_pdf_universal(fecha, df, titulo_reporte="REPORTE"):
    pdf = ProduccionPDF()
    pdf.add_page()
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"{titulo_reporte} - {fecha}", 1, 1, 'C', True)
    pdf.ln(5)
    pdf.set_fill_color(144, 238, 144)
    pdf.set_font("Helvetica", 'B', 9)
    cols = df.columns.tolist()
    ancho_celda = 190 / len(cols)
    for col in cols:
        pdf.cell(ancho_celda, 10, str(col), 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 8)
    for _, row in df.iterrows():
        for col in cols:
            texto = str(row[col])
            mostrar = (texto[:20] + '..') if len(texto) > 20 else texto
            pdf.cell(ancho_celda, 8, mostrar, 1, 0, 'C')
        pdf.ln()
    if 'DOCENAS' in df.columns:
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 10, f"TOTAL: {df['DOCENAS'].sum():.1f} DOCENAS", 0, 1, 'R')
    return pdf.output(dest='S').encode('latin-1', errors='replace')

def generar_excel_descargable(diccionario_dfs):
    """
    Recibe un diccionario {'Nombre Hoja': DataFrame} 
    y retorna un objeto BytesIO con el archivo Excel.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for nombre_hoja, df in diccionario_dfs.items():
            df.to_excel(writer, index=False, sheet_name=nombre_hoja)
    return output.getvalue()

def enviar_whatsapp(mensaje):
    msg_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{TELEFONO_DESTINO}?text={msg_encoded}"

# --- FUNCIÓN PRINCIPAL RENDER ---
def render_medias_crudo():
    st.header("🧦 Producción y Mantenimiento de Planta")
    
    tab_dia, tab_mes, tab_mant = st.tabs(["📅 Registro Diario", "📊 Reporte Mensual", "🛠️ Mantenimiento"])
    items_list = ["Soporte Lycra", "Soporte Stretch", "Pantalon Lycra", "Panty Grande", "Panty Mediano", "Pantalon Stretch"]

    # --- 1. PESTAÑA: REGISTRO Y DIARIO ---
    with tab_dia:
        st.subheader("📝 Nuevo Registro de Producción")
        with st.form("form_planchado", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1: f_reg = st.date_input("Fecha:", datetime.now())
            with col2: n_maq = st.number_input("# Máquina", min_value=1, step=1)
            with col3: item = st.selectbox("ITEM", items_list)
            with col4: part = st.number_input("# Partidas", min_value=1, step=1)
            doc = st.number_input("Docenas", min_value=0.1, step=0.5, format="%.1f")
            
            if st.form_submit_button("📥 Guardar Registro", use_container_width=True):
                ejecutar_consulta("INSERT INTO produccion_crudo (fecha, n_maquina, item, n_partidas, docenas) VALUES (?, ?, ?, ?, ?)", 
                                 (f_reg.strftime('%Y-%m-%d'), n_maq, item, part, doc))
                st.success("✅ Registro guardado"); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("🔍 Consulta y Exportación Diaria")
        f_busq = st.date_input("Seleccione día:", datetime.now(), key="busq_diaria")
        df_dia = obtener_datos("SELECT n_maquina as 'MAQ', item as ITEM, n_partidas as 'PART', docenas as DOCENAS FROM produccion_crudo WHERE fecha = ?", (f_busq.strftime('%Y-%m-%d'),))
        
        if not df_dia.empty:
            st.dataframe(df_dia, use_container_width=True, hide_index=True)
            
            # WhatsApp Texto
            texto_wa = f"*Reporte Diario - {f_busq}*\n\n"
            for _, r in df_dia.iterrows(): texto_wa += f"• Maq {r['MAQ']} | {r['ITEM']}: {r['DOCENAS']} Doc.\n"
            texto_wa += f"\n*Total: {df_dia['DOCENAS'].sum():.1f} Docenas*"
            
            st.link_button("🟢 Enviar por WhatsApp", enviar_whatsapp(texto_wa), use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                pdf_d = generar_pdf_universal(f_busq.strftime('%d/%m/%Y'), df_dia, "PRODUCCION DIARIA")
                st.download_button("📄 Descargar PDF", data=pdf_d, file_name=f"Produccion_{f_busq}.pdf", use_container_width=True)
            with c2:
                exc_d = generar_excel_descargable({"Produccion_Dia": df_dia})
                st.download_button("📗 Descargar Excel", data=exc_d, file_name=f"Produccion_{f_busq}.xlsx", use_container_width=True)
        else:
            st.info("No hay datos para esta fecha.")

    # --- 2. PESTAÑA: REPORTE MENSUAL ---
    with tab_mes:
        st.subheader("📊 Consolidado Mensual")
        cm, ca = st.columns(2)
        with cm: m_sel = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 1)
        with ca: a_sel = st.selectbox("Año", [2024, 2025, 2026], index=2)

        df_m_item = obtener_datos("SELECT item as ITEM, SUM(docenas) as DOCENAS FROM produccion_crudo WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=? GROUP BY item", (f"{m_sel:02d}", str(a_sel)))
        df_m_maq = obtener_datos("SELECT n_maquina as MAQ, SUM(docenas) as DOCENAS FROM produccion_crudo WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=? GROUP BY n_maquina ORDER BY DOCENAS DESC", (f"{m_sel:02d}", str(a_sel)))

        if not df_m_item.empty:
            st.metric("TOTAL MENSUAL", f"{df_m_item['DOCENAS'].sum():.1f} DOCENAS")
            g1, g2 = st.columns(2)
            with g1: st.bar_chart(df_m_item.set_index('ITEM'))
            with g2: st.bar_chart(df_m_maq.set_index('MAQ'), color="#ffaa00")
            
            # Exportaciones Mensuales
            pdf_m = generar_pdf_universal(f"{m_sel}/{a_sel}", df_m_item, "CONSOLIDADO MENSUAL")
            exc_m = generar_excel_descargable({"Resumen_Prendas": df_m_item, "Resumen_Maquinas": df_m_maq})
            
            c_m1, c_m2 = st.columns(2)
            with c_m1: st.download_button("📄 PDF Mensual", data=pdf_m, file_name=f"Mensual_{m_sel}.pdf", use_container_width=True)
            with c_m2: st.download_button("📗 Excel Mensual", data=exc_m, file_name=f"Mensual_{m_sel}.xlsx", use_container_width=True)
        else:
            st.warning("Sin datos para este periodo.")

    # --- 3. PESTAÑA: MANTENIMIENTO ---
    with tab_mant:
        st.subheader("🛠️ Control de Mantenimiento")
        with st.form("form_mant", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                f_serv = st.date_input("Fecha:", datetime.now())
                n_m_s = st.number_input("Máquina #:", min_value=1, step=1)
            with col_m2:
                tipo = st.selectbox("Tipo:", ["Preventivo", "Correctivo", "Limpieza", "Repuesto"])
                tecnico = st.text_input("Técnico:")
            detalle = st.text_area("Descripción:")
            if st.form_submit_button("🔧 Registrar Mantenimiento", use_container_width=True):
                ejecutar_consulta("INSERT INTO mantenimiento (fecha, n_maquina, tipo, detalle, tecnico) VALUES (?,?,?,?,?)", 
                                 (f_serv.strftime('%Y-%m-%d'), n_m_s, tipo, detalle, tecnico))
                st.success("Guardado"); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("📋 Historial Filtrado")
        cf1, cf2, cf3 = st.columns(3)
        with cf1: mh = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 1, key="mh_m")
        with cf2: ah = st.selectbox("Año", [2024, 2025, 2026], index=2, key="ah_m")
        with cf3:
            maq_db = obtener_datos("SELECT DISTINCT n_maquina FROM mantenimiento")
            opciones = ["Todas"] + ([str(m[0]) for m in maq_db.values] if not maq_db.empty else [])
            maq_f = st.selectbox("Máquina:", opciones)

        sql = "SELECT fecha as Fecha, n_maquina as MAQ, tipo as Tipo, tecnico as Tecnico, detalle as Detalle FROM mantenimiento WHERE strftime('%m', fecha)=? AND strftime('%Y', fecha)=?"
        params = [f"{mh:02d}", str(ah)]
        if maq_f != "Todas": sql += " AND n_maquina = ?"; params.append(int(maq_f))
        
        df_h = obtener_datos(sql + " ORDER BY fecha DESC", tuple(params))
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
            
            pdf_h = generar_pdf_universal(f"{mh}/{ah}", df_h, f"MANTENIMIENTO MAQ {maq_f}")
            exc_h = generar_excel_descargable({"Historial_Mantenimiento": df_h})
            
            c_h1, c_h2 = st.columns(2)
            with c_h1: st.download_button("📄 PDF Historial", data=pdf_h, file_name=f"Mant_{maq_f}.pdf", use_container_width=True)
            with c_h2: st.download_button("📗 Excel Historial", data=exc_h, file_name=f"Mant_{maq_f}.xlsx", use_container_width=True)