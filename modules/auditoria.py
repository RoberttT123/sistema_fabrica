import streamlit as st
import pandas as pd
from modules.database import obtener_datos
from datetime import datetime

def render_auditoria():
    st.header("🕵️ Auditoría de Sistema")
    st.info("Este panel muestra los movimientos realizados en la base de datos con paginación dinámica.")

    # --- INICIALIZAR ESTADO DE PAGINACIÓN ---
    if 'limite_logs' not in st.session_state:
        st.session_state.limite_logs = 10

    # --- FILTROS DE BÚSQUEDA ---
    col1, col2 = st.columns(2)
    with col1:
        filtro_usuario = st.text_input("👤 Filtrar por Usuario", placeholder="Ej: Juan...")
    with col2:
        filtro_accion = st.selectbox("⚡ Filtrar por Acción", 
                                    ["Todos", "INSERT", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "PRODUCCION", "MANTENIMIENTO"])

    # Resetear el límite si se cambia un filtro para evitar confusiones
    if st.button("Limpiar Filtros"):
        st.session_state.limite_logs = 10
        st.rerun()

    # --- CONSULTA SQL ---
    # Nota: Quitamos el LIMIT fijo del SQL para manejarlo con el session_state
    query = """
        SELECT 
            fecha_hora AS "Fecha_Raw", 
            nombre_usuario AS "Usuario", 
            accion AS "Accion", 
            tabla_afectada AS "Tabla", 
            detalle AS "Movimiento" 
        FROM log_actividades 
        WHERE 1=1
    """
    
    params = []
    if filtro_usuario:
        query += " AND nombre_usuario ILIKE %s"
        params.append(f"%{filtro_usuario}%")
    
    if filtro_accion != "Todos":
        query += " AND accion = %s"
        params.append(filtro_accion)
    
    query += " ORDER BY fecha_hora DESC"

    try:
        # 1. Obtener todos los datos que coinciden con el filtro para saber el TOTAL
        todos_los_logs = obtener_datos(query, tuple(params) if params else None)

        if todos_los_logs is not None and not todos_los_logs.empty:
            total_registros = len(todos_los_logs)
            
            # 2. Cortar el DataFrame según el límite actual
            logs_paginados = todos_los_logs.head(st.session_state.limite_logs).copy()

            # 3. Procesar fechas
            logs_paginados['Fecha_Raw'] = pd.to_datetime(logs_paginados['Fecha_Raw'])
            logs_paginados['Fecha'] = logs_paginados['Fecha_Raw'].dt.strftime('%d/%m/%Y %H:%M:%S')
            
            display_df = logs_paginados[['Fecha', 'Usuario', 'Accion', 'Tabla', 'Movimiento']]
            
            # 4. Mostrar la tabla
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # --- CONTROLES DE PAGINACIÓN ---
            mostrando = len(display_df)
            st.write(f"**Mostrando {mostrando} de {total_registros} registros.**")

            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                if mostrando < total_registros:
                    if st.button("Ver 10 más ➕"):
                        st.session_state.limite_logs += 10
                        st.rerun()
                else:
                    st.success("✨ Has llegado al final de los registros.")
            
            with col_btn2:
                if st.session_state.limite_logs > 10:
                    if st.button("Restablecer a 10 🔄"):
                        st.session_state.limite_logs = 10
                        st.rerun()

        else:
            st.warning("No se encontraron registros en la tabla 'log_actividades'.")

    except Exception as e:
        st.error(f"❌ Error visualizando logs: {e}")

    # --- ZONA DE RESPALDO ---
    st.divider()
    with st.expander("📥 Exportar Historial Completo"):
        if 'todos_los_logs' in locals() and todos_los_logs is not None and not todos_los_logs.empty:
            csv = todos_los_logs.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar TODOS los resultados (CSV)",
                data=csv,
                file_name=f"auditoria_completa_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )