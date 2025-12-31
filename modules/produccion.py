import streamlit as st
from modules.database import ejecutar_consulta, obtener_datos

def render_produccion():
    st.header("🏭 Proceso de Producción")
    
    tab1, tab2, tab3 = st.tabs(["1. Creación (Crudo)", "2. Costura", "3. Teñido"])

    # --- TAB 1: CREACIÓN EN CRUDO ---
    with tab1:
        st.subheader("Registrar Medias en Crudo")
        cantidad = st.number_input("Docenas fabricadas", min_value=1, step=1)
        if st.button("Registrar Lote Crudo"):
            query = "INSERT INTO lotes (cantidad_docenas, estado, color) VALUES (?, 'Crudo', 'Blanco')"
            ejecutar_consulta(query, (cantidad,))
            st.success(f"Lote de {cantidad} docenas en crudo registrado.")

    # --- TAB 2: COSTURA ---
    with tab2:
        st.subheader("Costura de Puntas")
        df_crudo = obtener_datos("SELECT id, cantidad_docenas, fecha_inicio FROM lotes WHERE estado = 'Crudo'")
        if not df_crudo.empty:
            st.write("Lotes esperando costura:")
            st.dataframe(df_crudo, use_container_width=True)
            lote_id = st.selectbox("Seleccione ID de lote para marcar como COSTURADO", df_crudo['id'])
            if st.button("Finalizar Costura"):
                ejecutar_consulta("UPDATE lotes SET estado = 'Costurado' WHERE id = ?", (lote_id,))
                st.rerun()
        else:
            st.info("No hay lotes en crudo para costurar.")

    # --- TAB 3: TEÑIDO ---
    with tab3:
        st.subheader("Proceso de Teñido")
        colores = ["Negro", "Café", "Vicuña", "Gris", "Azul", "Verde", "Bordo", "Beige", "Canela", "Blanco"]
        df_costurado = obtener_datos("SELECT id, cantidad_docenas FROM lotes WHERE estado = 'Costurado'")
        
        if not df_costurado.empty:
            lote_id_t = st.selectbox("Seleccione Lote para Teñir", df_costurado['id'])
            color_elegido = st.selectbox("Seleccione el color solicitado por el cliente", colores)
            cliente = st.text_input("Nombre del Cliente")
            
            if st.button("Registrar Teñido"):
                query = "UPDATE lotes SET estado = 'Teñido', color = ?, id_cliente_asignado = ? WHERE id = ?"
                ejecutar_consulta(query, (color_elegido, cliente, lote_id_t))
                st.success(f"Lote {lote_id_t} teñido de {color_elegido} para {cliente}")
                st.rerun()
        else:
            st.info("No hay lotes costurados listos para teñir.")