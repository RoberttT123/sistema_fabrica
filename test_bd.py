import os
import streamlit as st

# Verificar si el archivo de la base de datos existe en el servidor de la nube
db_path = 'sistema_ventas.db'

if os.path.exists(db_path):
    st.sidebar.success("✅ Base de datos conectada en la nube")
else:
    st.sidebar.error("❌ Archivo de base de datos no encontrado en el servidor")
    st.sidebar.info("Asegúrate de que 'sistema_ventas.db' esté subido a tu GitHub.")