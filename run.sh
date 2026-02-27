#!/bin/bash

# 1. Buscar si algo usa el puerto 8501 y cerrarlo (limpieza)
echo "🧹 Limpiando puerto 8501..."
lsof -ti:8501 | xargs kill -9 2>/dev/null

# 2. Activar el entorno virtual (venv)
source venv/bin/activate

# 3. Lanzar Streamlit
echo "🚀 Iniciando Sistema de Ventas..."
python3 -m streamlit run app_ventas.py --server.port 8501