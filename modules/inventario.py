import streamlit as st
import time
from datetime import datetime
# Importamos registrar_log
from modules.database import ejecutar_consulta, obtener_datos, registrar_log

def render_inventario():
    st.header("🧦 Inventario de Medias Terminadas")
    
    # 1. DEFINICIÓN DE LA ESTRUCTURA DE PRODUCTOS
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
        st.subheader("Existencias Actuales en Supabase")
        query_stock = """
            SELECT 
                id as ID, 
                linea as Línea, 
                tamano as Tipo, 
                nombre as Detalle, 
                color as Color, 
                cantidad as Cantidad, 
                precio_venta as Precio, 
                fecha_actualizacion as "Última Carga" 
            FROM inventario 
            ORDER BY id DESC
        """
        df = obtener_datos(query_stock)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros aún en la base de datos de la nube.")

    with tab_gestion:
        st.subheader("➕ Registrar Nuevo Producto")
        
        col_1, col_2, col_3 = st.columns(3)
        with col_1:
            linea_sel = st.selectbox("1. Seleccione Línea", list(ESTRUCTURA_PRODUCTOS.keys()))
        with col_2:
            tipos_disponibles = list(ESTRUCTURA_PRODUCTOS[linea_sel].keys())
            tipo_sel = st.selectbox("2. Seleccione Tipo", tipos_disponibles)
        with col_3:
            colores_disponibles = ESTRUCTURA_PRODUCTOS[linea_sel][tipo_sel]
            color_sel = st.selectbox("3. Seleccione Color", colores_disponibles)

        with st.form("form_nuevo_inv", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                cant = st.number_input("Cantidad inicial (Docenas)", min_value=0, step=1)
            with col_b:
                precio = st.number_input("Precio de Venta (Bs)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("🚀 Guardar en Supabase", use_container_width=True):
                hora_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                query = """
                    INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                ejecutar_consulta(query, (tipo_sel, linea_sel, tipo_sel, color_sel, cant, precio, hora_registro))
                
                # --- LOG DE REGISTRO ---
                registrar_log("INSERT", "inventario", f"Creó nuevo producto: {tipo_sel} {color_sel} - Cant: {cant}")
                
                st.success(f"✅ Registrado: {tipo_sel} - {color_sel}")
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        with st.expander("🛠️ MODIFICAR O ELIMINAR PRODUCTO"):
            id_sel = st.number_input("Ingrese ID del producto", min_value=1, step=1)
            datos = obtener_datos("SELECT * FROM inventario WHERE id = %s", (id_sel,))

            if not datos.empty:
                prod = datos.iloc[0]
                st.info(f"Editando: {prod['nombre']} ({prod['color']})")
                
                with st.form("form_edit_inv"):
                    e_col1, e_col2, e_col3 = st.columns(3)
                    with e_col1:
                        e_lin = st.text_input("Línea", value=str(prod['linea']))
                        e_tipo = st.text_input("Tipo", value=str(prod['tamano']))
                    with e_col2:
                        e_col = st.text_input("Color", value=str(prod['color']))
                        e_cant = st.number_input("Cantidad", value=int(prod['cantidad'] or 0))
                    with e_col3:
                        e_prec = st.number_input("Precio (Bs)", value=float(prod['precio_venta'] or 0.0))
                    
                    st.divider()
                    b1, b2, b3 = st.columns(3)
                    
                    if b1.form_submit_button("💾 Guardar"):
                        hora_edit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        query_upd = """
                            UPDATE inventario 
                            SET linea=%s, tamano=%s, color=%s, cantidad=%s, precio_venta=%s, fecha_actualizacion=%s 
                            WHERE id=%s
                        """
                        ejecutar_consulta(query_upd, (e_lin, e_tipo, e_col, e_cant, e_prec, hora_edit, int(id_sel)))
                        
                        # --- LOG DE EDICIÓN ---
                        registrar_log("UPDATE", "inventario", f"Editó ID {id_sel}: Nuevo stock {e_cant}, Precio {e_prec}")
                        
                        st.success("Cambios guardados"); time.sleep(1); st.rerun()

                    if b2.form_submit_button("👯 Duplicar"):
                        hora_dup = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        query_ins = """
                            INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        ejecutar_consulta(query_ins, (e_tipo, e_lin, e_tipo, e_col, e_cant, e_prec, hora_dup))
                        
                        # --- LOG DE DUPLICACIÓN ---
                        registrar_log("INSERT", "inventario", f"Duplicó producto ID {id_sel} como nuevo registro")
                        
                        st.success("Duplicado con éxito"); time.sleep(1); st.rerun()
                    
                    if b3.form_submit_button("🗑️ Eliminar", type="primary"):
                        ejecutar_consulta("DELETE FROM inventario WHERE id=%s", (int(id_sel),))
                        
                        # --- LOG DE ELIMINACIÓN ---
                        registrar_log("DELETE", "inventario", f"ELIMINÓ el producto ID {id_sel} ({e_tipo} {e_col})")
                        
                        st.warning("Eliminado de la base de datos"); time.sleep(1); st.rerun()