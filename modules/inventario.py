import streamlit as st
import time
from datetime import datetime
from modules.database import ejecutar_consulta, obtener_datos

def render_inventario():
    st.header("🧦 Inventario de Medias Terminadas")
    
    # 1. DEFINICIÓN DE LA ESTRUCTURA DE PRODUCTOS
    # Diccionario con Linea -> Tipos -> Colores
    ESTRUCTURA_PRODUCTOS = {
        "Lycra": {
            "Soporte Lycra": ["Romance", "Piel", "Coñac", "Tabaco", "Acacia", "Carbón", "Humo"],
            "Pantalon Lycra": ["Romance", "Piel", "Coñac", "Tabaco"]
        },
        "Panty": {
            "Panty Grande": ["Romance", "Piel", "Coñac", "Tabaco", "Negro", "Blanco"],
            "Panty Mediano": ["Romance", "Piel", "Coñac", "Tabaco", "Negro"]
        },
        "Stretch": {
            "Soporte Stretch": ["Hueso blanco", "Hueso rosado", "Beige", "Dumbo", "Romance", "Coñac", "Tabaco", "Cartón", "Acacia", "Calipso", "Chocolate", "Almendra", "Humo plata", "Humo oscuro", "Uva", "Api", "Carbón", "Negro"],
            "Pantalon Stretch": ["Hueso blanco", "Hueso rosado", "Beige", "Dumbo", "Romance", "Coñac", "Tabaco", "Cartón", "Acacia", "Calipso", "Chocolate", "Almendra", "Humo plata", "Humo oscuro", "Uva", "Api", "Carbón", "Negro"]
        }
    }

    tab_stock, tab_gestion = st.tabs(["📋 Stock en Bodega", "⚙️ Gestión de Inventario"])

    with tab_stock:
        st.subheader("Existencias Actuales")
        df = obtener_datos("SELECT id as ID, linea as Línea, tamano as Tipo, nombre as Detalle, color as Color, cantidad as Cantidad, precio_venta as Precio, fecha_actualizacion as 'Última Carga' FROM inventario ORDER BY fecha_actualizacion DESC")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay registros aún.")

    with tab_gestion:
        st.subheader("➕ Registrar Nuevo Producto")
        
        # Selectores fuera del Form para que sean dinámicos (Streamlit requiere esto para actualizar opciones)
        col_1, col_2, col_3 = st.columns(3)
        
        with col_1:
            linea_sel = st.selectbox("1. Seleccione Línea", list(ESTRUCTURA_PRODUCTOS.keys()))
        
        with col_2:
            tipos_disponibles = list(ESTRUCTURA_PRODUCTOS[linea_sel].keys())
            tipo_sel = st.selectbox("2. Seleccione Tipo", tipos_disponibles)
            
        with col_3:
            colores_disponibles = ESTRUCTURA_PRODUCTOS[linea_sel][tipo_sel]
            color_sel = st.selectbox("3. Seleccione Color", colores_disponibles)

        # Formulario para el resto de datos
        with st.form("form_nuevo_inv", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                cant = st.number_input("Cantidad inicial", min_value=0, step=1)
            with col_b:
                precio = st.number_input("Precio de Venta (Bs)", min_value=0.0, format="%.2f")
            
            detalle_final = f"{tipo_sel}" # El nombre se genera automáticamente
            
            if st.form_submit_button("🚀 Guardar en Inventario", use_container_width=True):
                hora_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                query = """
                    INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                # Guardamos 'tipo_sel' en la columna 'tamano' para mantener compatibilidad con tu DB
                ejecutar_consulta(query, (detalle_final, linea_sel, tipo_sel, color_sel, cant, precio, hora_registro))
                st.success(f"✅ Registrado: {detalle_final} - {color_sel}")
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        # --- SECCIÓN EDITAR/DUPLICAR ---
        with st.expander("🛠️ MODIFICAR O DUPLICAR PRODUCTO"):
            id_sel = st.number_input("Ingrese ID del producto", min_value=1, step=1)
            datos = obtener_datos("SELECT * FROM inventario WHERE id = ?", (id_sel,))

            if not datos.empty:
                prod = datos.iloc[0]
                st.info(f"Editando: {prod['nombre']} ({prod['color']})")
                
                # Para editar, usamos selectores simples para no complicar la lógica de edición rápida
                with st.form("form_edit_inv"):
                    e_col1, e_col2, e_col3 = st.columns(3)
                    with e_col1:
                        e_lin = st.selectbox("Línea", list(ESTRUCTURA_PRODUCTOS.keys()))
                        e_tipo = st.text_input("Tipo (Editable)", value=prod['tamano'])
                    with e_col2:
                        e_col = st.text_input("Color (Editable)", value=prod['color'])
                        e_cant = st.number_input("Cantidad", value=int(prod['cantidad']))
                    with e_col3:
                        e_prec = st.number_input("Precio (Bs)", value=float(prod['precio_venta'] or 0.0))
                    
                    st.divider()
                    b1, b2, b3 = st.columns(3)
                    
                    if b1.form_submit_button("💾 Guardar"):
                        hora_edit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ejecutar_consulta("UPDATE inventario SET linea=?, tamano=?, color=?, cantidad=?, precio_venta=?, fecha_actualizacion=? WHERE id=?", 
                                         (e_lin, e_tipo, e_col, e_cant, e_prec, hora_edit, id_sel))
                        st.success("Actualizado"); time.sleep(1); st.rerun()

                    if b2.form_submit_button("👯 Duplicar"):
                        hora_dup = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ejecutar_consulta("INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                         (e_tipo, e_lin, e_tipo, e_col, e_cant, e_prec, hora_dup))
                        st.success("Duplicado"); time.sleep(1); st.rerun()
                    
                    if b3.form_submit_button("🗑️ Eliminar", type="primary"):
                        ejecutar_consulta("DELETE FROM inventario WHERE id=?", (id_sel,))
                        st.warning("Eliminado"); time.sleep(1); st.rerun()