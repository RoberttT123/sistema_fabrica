import streamlit as st
import pandas as pd
import time
from modules.database import ejecutar_consulta, obtener_datos, registrar_log
from datetime import datetime, timedelta
from fpdf import FPDF
import os
import io
import urllib.parse
import locale

# --- CONFIGURACIÓN DE IDIOMA PARA FECHAS (Español) ---
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    # Si falla la configuración local, se usará inglés por defecto en algunas funciones,
    # pero el código auxiliar abajo lo corrige.
    pass
TELEFONO_DESTINO = "59178790265"
# --- CLASE PARA EL FORMATO DEL PDF ---
class ProduccionPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 23)
        self.set_font("Helvetica", 'B', 15)
        self.cell(0, 10, 'PRODUCCION EN CRUDO', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- FUNCIONES DE SOPORTE ---
def obtener_dia_literal(fecha_str):
    """Convierte fecha YYYY-MM-DD a YYYY-MM-DD - DIA"""
    dias = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = dias[fecha_obj.weekday()]
        return f"{fecha_str} - {dia_semana}"
    except:
        return fecha_str

def generar_pdf_universal(fecha_titulo, df, titulo_reporte="REPORTE"):
    pdf = ProduccionPDF()
    pdf.add_page()
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"{titulo_reporte} - {fecha_titulo}", 1, 1, 'C', True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
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
            # Especial para la columna fecha en reportes semanales/diarios
            if col == 'Fecha':
                texto = obtener_dia_literal(texto)
                
            mostrar = (texto[:25] + '..') if len(texto) > 25 else texto
            pdf.cell(ancho_celda, 8, mostrar, 1, 0, 'C')
        pdf.ln()
        
    if 'DOCENAS' in df.columns:
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 10, f"TOTAL: {df['DOCENAS'].sum():.1f} DOCENAS", 0, 1, 'R')
    
    resultado = pdf.output(dest='S')
    if isinstance(resultado, str):
        return resultado.encode('latin-1', errors='replace')
    return bytes(resultado)

def generar_excel_descargable(diccionario_dfs):
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
    st.header("🧶 Producción y Mantenimiento de Planta")
    
    tab_dia, tab_sem, tab_mes, tab_mant = st.tabs([
        "📅 Registro Diario", 
        "🗓️ Reporte Semanal",
        "📊 Reporte Mensual", 
        "🛠️ Mantenimiento"
    ])
    
    items_list = [
        "Soporte Lycra", "Soporte Lycra delgado", "Pantalón Lycra delgado",
        "Panty grande", "Panty mediano (10-12)", "Panty pequeño (4-6)",
        "Soporte stretch", "Pantalón stretch", "Tobillera stretch",
        "Soporte lujo", "Pantalón lujo", "Tobillera lujo",
        "Estrella", "Menudo", "Dolar", "Doble rombo", "Mariposa"
    ]

    # --- 1. PESTAÑA: REGISTRO DIARIO ---
    with tab_dia:
        st.subheader("📝 Nuevo Registro de Producción")
        with st.form("form_planchado", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1: f_reg = st.date_input("Fecha:", datetime.now())
            with col2: n_maq = st.number_input("# Máquina", min_value=1, step=1)
            with col3: item = st.selectbox("ITEM", items_list)
            with col4: part = st.number_input("# Partidas", min_value=1, step=1)
            doc = st.number_input("Docenas", min_value=0.1, step=0.5, format="%.1f")
            
            if st.form_submit_button("📥 Guardar Registro en la Nube", use_container_width=True):
                ejecutar_consulta(
                    "INSERT INTO produccion_crudo (fecha, n_maquina, item, n_partidas, docenas) VALUES (%s, %s, %s, %s, %s)", 
                    (f_reg.strftime('%Y-%m-%d'), n_maq, item, part, doc)
                )
                registrar_log("PRODUCCION", "produccion_crudo", f"Registró Maq {n_maq}: {doc} Doc. de {item}")
                st.success("✅ Registro guardado"); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("🔍 Consulta Diaria")
        f_busq = st.date_input("Seleccione día:", datetime.now(), key="busq_diaria")
        
        df_dia = obtener_datos(
            "SELECT n_maquina as \"MAQ\", item as \"ITEM\", n_partidas as \"PART\", docenas as \"DOCENAS\" FROM produccion_crudo WHERE fecha::date = %s", 
            (f_busq.strftime('%Y-%m-%d'),)
        )
        
        if not df_dia.empty:
            st.dataframe(df_dia, use_container_width=True, hide_index=True)
            
            texto_wa = f"*Reporte Diario - {f_busq}*\n\n"
            for _, r in df_dia.iterrows(): 
                texto_wa += f"• Maq {r['MAQ']} | {r['ITEM']}: {r['DOCENAS']} Doc.\n"
            texto_wa += f"\n*Total: {df_dia['DOCENAS'].sum():.1f} Docenas*"
            st.link_button("🟢 Enviar reporte por WhatsApp", enviar_whatsapp(texto_wa), use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                pdf_d = generar_pdf_universal(f_busq.strftime('%d/%m/%Y'), df_dia, "PRODUCCION DIARIA")
                st.download_button("📄 Descargar PDF", data=pdf_d, file_name=f"Produccion_{f_busq}.pdf", use_container_width=True)
            with c2:
                exc_d = generar_excel_descargable({"Produccion_Dia": df_dia})
                st.download_button("📗 Descargar Excel", data=exc_d, file_name=f"Produccion_{f_busq}.xlsx", use_container_width=True)
        else:
            st.info("No hay datos registrados para esta fecha.")

    # --- 2. PESTAÑA: REPORTE SEMANAL ---
    with tab_sem:
        st.subheader("🗓️ Producción Semanal")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fecha_inicio = st.date_input("Fecha Inicio", datetime.now() - timedelta(days=7), key="sem_ini")
        with col_s2:
            fecha_fin = st.date_input("Fecha Fin", datetime.now(), key="sem_fin")

        if fecha_inicio > fecha_fin:
            st.error("Error: La fecha de inicio no puede ser mayor a la fecha fin.")
        else:
            query_sem = """
                SELECT 
                    fecha::date as "Fecha", 
                    n_maquina as "MAQ", 
                    item as "ITEM", 
                    docenas as "DOCENAS" 
                FROM produccion_crudo 
                WHERE fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC, n_maquina ASC
            """
            df_sem = obtener_datos(query_sem, (fecha_inicio.strftime('%Y-%m-%d'), fecha_fin.strftime('%Y-%m-%d')))
            
            if not df_sem.empty:
                # Mostrar tabla en pantalla
                st.write(f"**Tabla de Producción del {fecha_inicio} al {fecha_fin}**")
                
                # Crear copia para mostrar en pantalla con el día literal
                df_display = df_sem.copy()
                df_display['Fecha'] = df_display['Fecha'].apply(lambda x: obtener_dia_literal(x.strftime('%Y-%m-%d')))
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                st.metric("TOTAL SEMANAL", f"{df_sem['DOCENAS'].sum():.1f} DOCENAS")
                
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    # El PDF ya maneja internamente el día literal gracias a la modificación en generar_pdf_universal
                    pdf_s = generar_pdf_universal(f"{fecha_inicio} al {fecha_fin}", df_sem, "REPORTE SEMANAL")
                    st.download_button("📄 PDF Semanal", data=pdf_s, file_name=f"Semanal_{fecha_inicio}.pdf", use_container_width=True)
                with c_s2:
                    exc_s = generar_excel_descargable({"Produccion_Semana": df_display})
                    st.download_button("📗 Excel Semanal", data=exc_s, file_name=f"Semanal_{fecha_inicio}.xlsx", use_container_width=True)
            else:
                st.info("No hay datos en el rango de fechas seleccionado.")

    # --- 3. PESTAÑA: REPORTE MENSUAL ---
    with tab_mes:
        st.subheader("📊 Producción Mensual")
        cm, ca = st.columns(2)
        with cm: m_sel = st.selectbox("Mes", range(1, 13), index=datetime.now().month - 1)
        with ca: a_sel = st.selectbox("Año", [2024, 2025, 2026], index=2)

        query_detallado = """
            SELECT fecha::date as "Fecha", n_maquina as "MAQ", item as "ITEM", docenas as "DOCENAS"
            FROM produccion_crudo 
            WHERE TO_CHAR(fecha, 'MM') = %s AND TO_CHAR(fecha, 'YYYY') = %s 
            ORDER BY fecha DESC
        """
        query_item = """
            SELECT item as "ITEM", SUM(docenas) as "DOCENAS" 
            FROM produccion_crudo 
            WHERE TO_CHAR(fecha, 'MM') = %s AND TO_CHAR(fecha, 'YYYY') = %s 
            GROUP BY item
        """
        query_maq = """
            SELECT n_maquina as "MAQ", SUM(docenas) as "DOCENAS" 
            FROM produccion_crudo 
            WHERE TO_CHAR(fecha, 'MM') = %s AND TO_CHAR(fecha, 'YYYY') = %s 
            GROUP BY n_maquina ORDER BY "DOCENAS" DESC
        """
        
        df_m_detalle = obtener_datos(query_detallado, (f"{m_sel:02d}", str(a_sel)))
        df_m_item = obtener_datos(query_item, (f"{m_sel:02d}", str(a_sel)))
        df_m_maq = obtener_datos(query_maq, (f"{m_sel:02d}", str(a_sel)))

        if not df_m_item.empty:
            st.write(f"**Tabla Detallada de Producción - Mes {m_sel}/{a_sel}**")
            
            # Formatear fecha para pantalla en mensual también
            df_m_display = df_m_detalle.copy()
            df_m_display['Fecha'] = df_m_display['Fecha'].apply(lambda x: obtener_dia_literal(x.strftime('%Y-%m-%d')))
            st.dataframe(df_m_display, use_container_width=True, hide_index=True)
            
            st.metric("TOTAL MENSUAL", f"{df_m_item['DOCENAS'].sum():.1f} DOCENAS")
            
            g1, g2 = st.columns(2)
            with g1: 
                st.write("**Resumen por Prenda**")
                st.bar_chart(df_m_item.set_index('ITEM'))
            with g2: 
                st.write("**Resumen por Máquina**")
                st.bar_chart(df_m_maq.set_index('MAQ'))
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                pdf_m = generar_pdf_universal(f"{m_sel}/{a_sel}", df_m_detalle, "CONSOLIDADO MENSUAL")
                st.download_button("📄 PDF Mensual", data=pdf_m, file_name=f"Mensual_{m_sel}.pdf", use_container_width=True)
            with c_m2:
                exc_m = generar_excel_descargable({
                    "Resumen_Prendas": df_m_item, 
                    "Resumen_Maquinas": df_m_maq,
                    "Detalle_Diario": df_m_display
                })
                st.download_button("📗 Excel Mensual", data=exc_m, file_name=f"Mensual_{m_sel}.xlsx", use_container_width=True)
        else:
            st.info("No hay datos para el mes seleccionado.")

    # --- 4. PESTAÑA: MANTENIMIENTO ---
    with tab_mant:
        st.subheader("🛠️ Registro de Mantenimiento")
        with st.form("form_mant", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                f_serv = st.date_input("Fecha Servicio:", datetime.now())
                n_m_s = st.number_input("Número Máquina:", min_value=1, step=1)
            with col_m2:
                tipo = st.selectbox("Tipo de Servicio:", ["Preventivo", "Correctivo", "Limpieza", "Repuesto"])
                tecnico = st.text_input("Nombre del Técnico:")
            detalle = st.text_area("Detalles del trabajo realizado:")
            
            if st.form_submit_button("🔧 Guardar Mantenimiento", use_container_width=True):
                ejecutar_consulta(
                    "INSERT INTO mantenimiento (fecha, n_maquina, tipo, detalle, tecnico) VALUES (%s,%s,%s,%s,%s)", 
                    (f_serv.strftime('%Y-%m-%d'), n_m_s, tipo, detalle, tecnico)
                )
                registrar_log("MANTENIMIENTO", "mantenimiento", f"Servicio {tipo} en Maq {n_m_s} por {tecnico}")
                st.success("Mantenimiento registrado correctamente"); time.sleep(1); st.rerun()

        st.divider()
        st.subheader("📋 Historial de Servicios")
        cf1, cf2, cf3 = st.columns(3)
        with cf1: mh = st.selectbox("Filtrar Mes", range(1, 13), index=datetime.now().month - 1, key="fmh")
        with cf2: ah = st.selectbox("Filtrar Año", [2024, 2025, 2026], index=2, key="fah")
        with cf3:
            maq_res = obtener_datos("SELECT DISTINCT n_maquina FROM mantenimiento ORDER BY n_maquina")
            opc_m = ["Todas"] + ([str(int(m)) for m in maq_res.iloc[:,0]] if not maq_res.empty else [])
            maq_f = st.selectbox("Filtrar Máquina:", opc_m, key="fmaq")

        sql_h = """
            SELECT id as \"ID\", fecha as \"Fecha\", n_maquina as \"MAQ\", tipo as \"Tipo\", 
                   tecnico as \"Tecnico\", detalle as \"Detalle\" 
            FROM mantenimiento 
            WHERE TO_CHAR(fecha, 'MM') = %s AND TO_CHAR(fecha, 'YYYY') = %s
        """
        params_h = [f"{mh:02d}", str(ah)]
        if maq_f != "Todas": 
            sql_h += " AND n_maquina = %s"
            params_h.append(int(maq_f))
        
        df_h = obtener_datos(sql_h + " ORDER BY fecha DESC", tuple(params_h))
        
        if not df_h.empty:
            st.dataframe(df_h, use_container_width=True, hide_index=True)
            
            # --- 🛡️ MEJORA DE SEGURIDAD: SOLO JEFE PUEDE BORRAR ---
            if st.session_state.rol == "Jefe":
                with st.expander("🗑️ Borrar registro de mantenimiento"):
                    id_borrar = st.number_input("ID del mantenimiento a eliminar", min_value=1, step=1)
                    if st.button("Confirmar Eliminación", type="primary"):
                        ejecutar_consulta("DELETE FROM mantenimiento WHERE id = %s", (id_borrar,))
                        registrar_log("DELETE", "mantenimiento", f"Eliminó registro de mantenimiento ID {id_borrar}")
                        st.warning(f"Registro {id_borrar} eliminado."); time.sleep(1); st.rerun()

            c_h1, c_h2 = st.columns(2)
            with c_h1:
                pdf_h = generar_pdf_universal(f"{mh}/{ah}", df_h, f"MANTENIMIENTO MAQ {maq_f}")
                st.download_button("📄 PDF Historial", data=pdf_h, file_name=f"Mant_{maq_f}.pdf", use_container_width=True)
            with c_h2:
                exc_h = generar_excel_descargable({"Historial_Mantenimiento": df_h})
                st.download_button("📗 Excel Historial", data=exc_h, file_name=f"Mant_{maq_f}.xlsx", use_container_width=True)
        else:
            st.info("No hay registros de mantenimiento en el periodo seleccionado.")