import streamlit as st
import time
from modules.database import ejecutar_consulta, obtener_datos

def render_inventario():
    st.header("🧦 Inventario de Medias Terminadas")
    
    tab_stock, tab_gestion = st.tabs(["📋 Stock en Bodega", "⚙️ Gestión de Inventario"])

    # --- TAB 1: VER STOCK ---
    with tab_stock:
        st.subheader("Existencias Actuales")
        # Usamos COALESCE en SQL para que si es NULL devuelva 'Sin especificar'
        query_ver = """
            SELECT 
                id as ID, 
                nombre as Detalle, 
                COALESCE(color, 'Sin especificar') as Color, 
                cantidad as Cantidad, 
                fecha_actualizacion as 'Última Carga' 
            FROM inventario
        """
        df = obtener_datos(query_ver)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay medias registradas en el inventario aún.")

    # --- TAB 2: AGREGAR / EDITAR / ELIMINAR ---
    with tab_gestion:
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.subheader("➕ Registrar Nuevo")
            with st.form("form_nuevo_inv", clear_on_submit=True):
                det = st.text_input("Detalle (ej. Media Escolar)")
                col = st.text_input("Color")
                cant = st.number_input("Cantidad", min_value=0, step=1)
                
                if st.form_submit_button("Guardar en Bodega"):
                    if det and col:
                        # Aseguramos que el color no sea solo espacios en blanco
                        color_final = col.strip() if col.strip() != "" else "Sin color"
                        query = "INSERT INTO inventario (nombre, color, cantidad, tipo) VALUES (?, ?, ?, 'Media')"
                        ejecutar_consulta(query, (det, color_final, cant))
                        st.success("✅ Registrado con éxito.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("⚠️ Completa Detalle y Color.")

        with col_der:
            st.subheader("📝 Editar o Eliminar")
            id_sel = st.number_input("ID del producto", min_value=1, step=1, key="id_inv_gest")
            datos = obtener_datos("SELECT * FROM inventario WHERE id = ?", (id_sel,))

            if not datos.empty:
                # Manejo del valor del color para el formulario de edición
                val_color_db = datos.iloc[0]['color']
                # Si el valor es None o nulo en Python, ponemos string vacío para el text_input
                val_color_input = str(val_color_db) if val_color_db is not None else ""

                with st.form("form_edit_inv"):
                    e_det = st.text_input("Detalle", value=datos.iloc[0]['nombre'])
                    e_col = st.text_input("Color", value=val_color_input)
                    e_cant = st.number_input("Cantidad", value=int(datos.iloc[0]['cantidad']))
                    
                    btn1, btn2 = st.columns(2)
                    if btn1.form_submit_button("💾 Actualizar"):
                        color_editado = e_col.strip() if e_col.strip() != "" else "Sin color"
                        ejecutar_consulta("UPDATE inventario SET nombre=?, color=?, cantidad=? WHERE id=?", (e_det, color_editado, e_cant, id_sel))
                        st.success("Actualizado.")
                        time.sleep(1)
                        st.rerun()
                    
                    if btn2.form_submit_button("🗑️ Eliminar"):
                        ejecutar_consulta("DELETE FROM inventario WHERE id=?", (id_sel,))
                        st.warning("Eliminado.")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("Selecciona un ID válido para editar.")