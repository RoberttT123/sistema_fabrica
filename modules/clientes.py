import streamlit as st
import time
import os
from modules.database import ejecutar_consulta, obtener_datos
from fpdf import FPDF

class ClientePDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33)
        
        # Helvetica es más segura para servidores Linux (Streamlit Cloud)
        self.set_font("Helvetica", 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'REPORTE DE VENTAS POR CLIENTE', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf_mejorado(datos, historial):
    pdf = ClientePDF()
    pdf.add_page()
    
    # --- Datos del Cliente ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"INFORMACION DEL CLIENTE", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", '', 11)
    # Limpiamos posibles caracteres especiales para evitar errores en latin-1
    nombre_c = str(datos['Cliente']).encode('ascii', 'ignore').decode('ascii')
    
    pdf.cell(95, 8, f"Nombre: {nombre_c}", 1)
    pdf.cell(95, 8, f"ID: {datos['ID']}", 1, 1)
    pdf.cell(95, 8, f"Telefono: {datos['Telefono']}", 1)
    pdf.cell(95, 8, f"Edad: {datos['Edad']} anos", 1, 1)
    pdf.cell(0, 8, f"Direccion: {str(datos['Direccion'])[:50]}", 1, 1)
    pdf.ln(10)
    
    # --- Tabla de Historial ---
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"HISTORIAL DE COMPRAS", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(40, 8, "Fecha", 1, 0, 'C', True)
    pdf.cell(80, 8, "Producto", 1, 0, 'C', True)
    pdf.cell(30, 8, "Cant.", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total (Bs)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 10)
    for _, row in historial.iterrows():
        pdf.cell(40, 7, str(row['Fecha'])[:10], 1, 0, 'C')
        pdf.cell(80, 7, str(row['Producto'])[:30], 1, 0, 'L')
        pdf.cell(30, 7, str(row['Cant']), 1, 0, 'C')
        pdf.cell(40, 7, f"{row['Total']:.2f}", 1, 1, 'R')
    
    # Total Final
    pdf.set_font("Helvetica", 'B', 11)
    total_acumulado = historial['Total'].sum()
    pdf.cell(150, 10, "INVERSION TOTAL ACUMULADA:", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'R', True)
    
    # --- BLOQUE DE COMPATIBILIDAD UNIVERSAL ---
    resultado = pdf.output(dest='S')
    if isinstance(resultado, (bytes, bytearray)):
        return bytes(resultado)
    return resultado.encode('latin-1', errors='replace')

@st.dialog("📜 Historial de Ventas")
def mostrar_modal_historial(datos, df_h):
    st.write(f"### Detalle: {datos['Cliente']}")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
    
    total = df_h['Total'].sum()
    st.metric("Inversión Total", f"{total:.2f} Bs")
    
    try:
        pdf_bytes = generar_pdf_mejorado(datos, df_h)
        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_bytes,
            file_name=f"Reporte_{datos['Cliente']}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"btn_pdf_{datos['ID']}"
        )
    except Exception as e:
        st.error(f"Error al generar PDF: {e}")

def render_clientes():
    st.header("🛍️ Cartera de Clientes")

    query = """
        SELECT c.id_cliente as ID, c.nombre as Cliente, c.direccion as Direccion, 
               c.telefono as Telefono, c.edad as Edad,
               (SELECT COUNT(*) FROM pedidos WHERE id_cliente = c.id_cliente) as Total_Ventas
        FROM clientes c
    """
    df_clientes = obtener_datos(query)

    if not df_clientes.empty:
        df_clientes["Acciones"] = df_clientes["Total_Ventas"].apply(
            lambda x: "📜 Ver Historial | 📄 PDF" if x > 0 else "👤 Sin Compras"
        )

        st.subheader("📋 Lista General de Clientes")
        st.info("💡 Haga clic en la fila de un cliente para ver su historial.")

        event = st.dataframe(
            df_clientes.drop(columns=["Total_Ventas"]),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        if event and "selection" in event and event["selection"]["rows"]:
            idx = event["selection"]["rows"][0]
            cliente_sel = df_clientes.iloc[idx]
            
            query_h = """
                SELECT p.fecha as Fecha, i.nombre as Producto, p.cantidad as Cant, p.precio as Total 
                FROM pedidos p 
                JOIN inventario i ON p.id_inventario = i.id 
                WHERE p.id_cliente = ? ORDER BY p.fecha DESC
            """
            df_h = obtener_datos(query_h, (int(cliente_sel['ID']),))

            if not df_h.empty:
                mostrar_modal_historial(cliente_sel, df_h)
            else:
                st.toast(f"El cliente {cliente_sel['Cliente']} no tiene compras.", icon="⚠️")
    else:
        st.info("No hay clientes registrados.")

    st.divider()

    st.subheader("👤 Registrar Nuevo Cliente")
    with st.form("nuevo_cli", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nombre / Razón Social")
            dir = st.text_input("Dirección")
        with col2:
            tel = st.text_input("Teléfono")
            ed = st.number_input("Edad", min_value=0, value=30)
        
        if st.form_submit_button("✅ Guardar Cliente", use_container_width=True):
            if nom:
                ejecutar_consulta("INSERT INTO clientes (nombre, edad, direccion, telefono) VALUES (?,?,?,?)", (nom, ed, dir, tel))
                st.success("Cliente registrado."); time.sleep(1); st.rerun()
            else:
                st.error("El nombre es obligatorio.")