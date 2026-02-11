import streamlit as st
import time
import os
from modules.database import ejecutar_consulta, obtener_datos
from fpdf import FPDF

class ClientePDF(FPDF):
    def header(self):
        # Logo: Verificar si existe el archivo
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 33)
        
        self.set_font("Arial", 'B', 15)
        # Mover a la derecha para no chocar con el logo
        self.cell(80)
        self.cell(30, 10, 'REPORTE DE VENTAS POR CLIENTE', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_mejorado(datos, historial):
    pdf = ClientePDF()
    pdf.add_page()
    
    # --- Datos del Cliente ---
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"INFORMACIÓN DEL CLIENTE", 1, 1, 'L', True)
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(95, 8, f"Nombre: {datos['Cliente']}", 1)
    pdf.cell(95, 8, f"ID: {datos['ID']}", 1, 1)
    pdf.cell(95, 8, f"Teléfono: {datos['Telefono']}", 1)
    pdf.cell(95, 8, f"Edad: {datos['Edad']} años", 1, 1)
    pdf.cell(0, 8, f"Dirección: {datos['Direccion']}", 1, 1)
    pdf.ln(10)
    
    # --- Tabla de Historial ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"HISTORIAL DE COMPRAS", 1, 1, 'L', True)
    
    # Encabezados de tabla
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 8, "Fecha", 1, 0, 'C', True)
    pdf.cell(80, 8, "Producto", 1, 0, 'C', True)
    pdf.cell(30, 8, "Cant.", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total (Bs)", 1, 1, 'C', True)
    
    # Filas
    pdf.set_font("Arial", '', 10)
    for _, row in historial.iterrows():
        pdf.cell(40, 7, str(row['Fecha']), 1, 0, 'C')
        pdf.cell(80, 7, str(row['Producto']), 1, 0, 'L')
        pdf.cell(30, 7, str(row['Cant']), 1, 0, 'C')
        pdf.cell(40, 7, f"{row['Total']:.2f}", 1, 1, 'R')
    
    # Total Final
    pdf.set_font("Arial", 'B', 11)
    total_acumulado = historial['Total'].sum()
    pdf.cell(150, 10, "INVERSIÓN TOTAL ACUMULADA:", 1, 0, 'R', True)
    pdf.cell(40, 10, f"{total_acumulado:.2f} Bs", 1, 1, 'R', True)
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

@st.dialog("📜 Historial de Ventas")
def mostrar_modal_historial(datos, df_h):
    st.write(f"### Detalle: {datos['Cliente']}")
    st.dataframe(df_h, use_container_width=True, hide_index=True)
    
    total = df_h['Total'].sum()
    st.metric("Inversión Total", f"{total:.2f} Bs")
    
    pdf_bytes = generar_pdf_mejorado(datos, df_h)
    st.download_button(
        label="📥 Descargar Reporte PDF con Logo",
        data=pdf_bytes,
        file_name=f"Reporte_{datos['Cliente']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

def render_clientes():
    st.header("🛍️ Cartera de Clientes")

    # SQL para traer clientes y saber si tienen ventas
    query = """
        SELECT c.id_cliente as ID, c.nombre as Cliente, c.direccion as Direccion, 
               c.telefono as Telefono, c.edad as Edad,
               (SELECT COUNT(*) FROM pedidos WHERE id_cliente = c.id_cliente) as Total_Ventas
        FROM clientes c
    """
    df_clientes = obtener_datos(query)

    if not df_clientes.empty:
        # Columna de acciones con lógica de negocio
        df_clientes["Acciones"] = df_clientes["Total_Ventas"].apply(
            lambda x: "📜 Ver Historial | 📄 PDF" if x > 0 else "👤 Sin Compras"
        )

        st.subheader("📋 Lista General de Clientes")
        st.info("💡 Haga clic en la fila de un cliente para ver su historial y descargar el PDF.")

        # Tabla interactiva con selección de fila única
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
            
            # Obtener historial real
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
                st.toast(f"El cliente {cliente_sel['Cliente']} aún no registra compras.", icon="⚠️")
    else:
        st.info("No hay clientes en la base de datos.")

    st.divider()

    # --- Registro de Clientes ---
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