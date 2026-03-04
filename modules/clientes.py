import streamlit as st
import time
import os
import pandas as pd
from modules.database import ejecutar_consulta, obtener_datos, registrar_log
from fpdf import FPDF

# --- CLASE PARA EL FORMATO DEL PDF ---
class ClientePDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 4, 22)
        
        self.set_font("Helvetica", 'B', 15)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, 'REPORTE DE VENTAS POR CLIENTE', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# --- FUNCIONES DE SOPORTE ---
def generar_pdf_mejorado(datos, historial):
    pdf = ClientePDF()
    pdf.add_page()
    
    # --- Datos del Cliente ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"INFORMACION DEL CLIENTE", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", '', 11)
    def clean(text):
        # Limpieza básica para evitar errores de codificación en FPDF latin-1
        return str(text).replace('ñ', 'n').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('Ñ', 'N')

    pdf.cell(95, 8, clean(f"Nombre: {datos['Cliente']}"), 1)
    pdf.cell(95, 8, f"ID Cliente: {datos['ID']}", 1, 1)
    pdf.cell(95, 8, clean(f"Telefono: {datos['Telefono']}"), 1)
    pdf.cell(95, 8, clean(f"Ciudad: {datos['Ciudad']}"), 1, 1)
    pdf.cell(0, 8, clean(f"Direccion: {datos['Direccion']}"), 1, 1)
    pdf.ln(10)
    
    # --- Tabla de Historial ---
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"HISTORIAL DE COMPRAS", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(40, 8, "Fecha", 1, 0, 'C', True)
    pdf.cell(80, 8, "Producto", 1, 0, 'C', True)
    pdf.cell(30, 8, "Cant.", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total (Bs)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 10)
    for _, row in historial.iterrows():
        fecha_str = str(row['Fecha'])[:10]
        pdf.cell(40, 7, fecha_str, 1, 0, 'C')
        pdf.cell(80, 7, clean(row['Producto'])[:30], 1, 0, 'L')
        pdf.cell(30, 7, str(row['Cant']), 1, 0, 'C')
        pdf.cell(40, 7, f"{float(row['Total']):.2f}", 1, 1, 'R')
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    total_acumulado = historial['Total'].sum()
    pdf.cell(150, 10, "INVERSION TOTAL ACUMULADA:", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'R', True)
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

@st.dialog("📜 Historial de Ventas")
def mostrar_modal_historial(cliente_info, df_h):
    st.write(f"### Detalle: {cliente_info['Cliente']}")
    df_h['Fecha'] = pd.to_datetime(df_h['Fecha']).dt.strftime('%d/%m/%Y')
    st.dataframe(df_h, use_container_width=True, hide_index=True)
    
    total = df_h['Total'].sum()
    st.metric("Inversión Total Acumulada", f"{total:.2f} Bs")
    
    try:
        pdf_bytes = generar_pdf_mejorado(cliente_info, df_h)
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_bytes,
            file_name=f"Reporte_{cliente_info['Cliente']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"No se pudo generar el PDF: {e}")

def render_clientes():
    st.header("🛍️ Cartera de Clientes")

    # --- OBTENER DEPARTAMENTOS PARA LOS SELECTORES ---
    df_deptos = obtener_datos("SELECT * FROM departamentos ORDER BY nombre ASC")
    depto_opciones = {row['nombre']: row['id_depto'] for _, row in df_deptos.iterrows()}

    # --- LISTA DE CLIENTES ---
    query = """
        SELECT c.id_cliente as "ID", c.nombre as "Cliente", d.nombre as "Ciudad",
               c.direccion as "Direccion", c.telefono as "Telefono", c.edad as "Edad",
               (SELECT COUNT(*) FROM pedidos WHERE id_cliente = c.id_cliente) as "Ventas"
        FROM clientes c
        JOIN departamentos d ON c.id_depto = d.id_depto
        ORDER BY c.nombre ASC
    """
    
    try:
        df_clientes = obtener_datos(query)
        if not df_clientes.empty:
            st.subheader("📋 Lista General de Clientes")
            event = st.dataframe(
                df_clientes,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            if event and event.get("selection") and event["selection"]["rows"]:
                idx = event["selection"]["rows"][0]
                cliente_sel = df_clientes.iloc[idx]
                
                # Buscamos historial con el ID del cliente
                query_h = """
                    SELECT p.fecha as "Fecha", i.nombre as "Producto", 
                           p.cantidad as "Cant", p.precio as "Total" 
                    FROM pedidos p 
                    JOIN inventario i ON p.id_inventario = i.id 
                    WHERE p.id_cliente = %s 
                    ORDER BY p.fecha DESC
                """
                df_h = obtener_datos(query_h, (int(cliente_sel['ID']),))
                if not df_h.empty:
                    mostrar_modal_historial(cliente_sel, df_h)
                else:
                    st.toast(f"El cliente {cliente_sel['Cliente']} aún no tiene compras.", icon="ℹ️")
        else:
            st.info("Aún no hay clientes registrados.")
    except Exception as e:
        st.error(f"Error al cargar clientes: {e}")

    st.divider()

    # --- REGISTRO Y EDICIÓN ---
    col_reg, col_edit = st.columns(2)

    with col_reg:
        st.subheader("👤 Nuevo Cliente")
        with st.form("nuevo_cli", clear_on_submit=True):
            nom = st.text_input("Nombre o Razón Social")
            tel = st.text_input("Teléfono")
            depto_nom = st.selectbox("Departamento", options=list(depto_opciones.keys()))
            dir_cli = st.text_input("Dirección")
            ed = st.number_input("Edad", 0, 120, 30)
            
            if st.form_submit_button("✅ Guardar Cliente", use_container_width=True):
                if nom.strip():
                    id_d = depto_opciones[depto_nom]
                    ejecutar_consulta(
                        "INSERT INTO clientes (nombre, edad, direccion, telefono, id_depto) VALUES (%s,%s,%s,%s,%s)", 
                        (nom, ed, dir_cli, tel, id_d)
                    )
                    registrar_log("INSERT", "clientes", f"Registró nuevo cliente: {nom} en {depto_nom}")
                    st.success(f"¡{nom} registrado!")
                    time.sleep(1); st.rerun()

    with col_edit:
        st.subheader("🛠️ Editar / Eliminar")
        id_edit = st.number_input("ID del Cliente a modificar", min_value=1, step=1)
        if id_edit:
            res = obtener_datos("SELECT * FROM clientes WHERE id_cliente = %s", (id_edit,))
            if not res.empty:
                cli = res.iloc[0]
                with st.form("edit_cli"):
                    enom = st.text_input("Nombre", value=cli['nombre'])
                    etel = st.text_input("Teléfono", value=cli['telefono'])
                    edir = st.text_input("Dirección", value=cli['direccion'])
                    
                    # Obtener nombre del departamento actual
                    depto_actual_query = obtener_datos("SELECT nombre FROM departamentos WHERE id_depto = %s", (int(cli['id_depto']),))
                    nombre_d_actual = depto_actual_query.iloc[0]['nombre'] if not depto_actual_query.empty else list(depto_opciones.keys())[0]
                    
                    enuevo_depto = st.selectbox("Departamento", options=list(depto_opciones.keys()), 
                                               index=list(depto_opciones.keys()).index(nombre_d_actual))
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Actualizar"):
                        id_d_nuevo = depto_opciones[enuevo_depto]
                        ejecutar_consulta(
                            "UPDATE clientes SET nombre=%s, direccion=%s, telefono=%s, id_depto=%s WHERE id_cliente=%s",
                            (enom, edir, etel, id_d_nuevo, id_edit)
                        )
                        registrar_log("UPDATE", "clientes", f"Editó datos del cliente ID {id_edit}")
                        st.success("Actualizado"); time.sleep(1); st.rerun()
                        
                    if b2.form_submit_button("🗑️ Eliminar", type="primary"):
                        ejecutar_consulta("DELETE FROM clientes WHERE id_cliente=%s", (id_edit,))
                        registrar_log("DELETE", "clientes", f"ELIMINÓ al cliente ID {id_edit}")
                        st.warning("Eliminado"); time.sleep(1); st.rerun()