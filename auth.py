import streamlit as st
import requests
import os

import os
import streamlit as st

API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:3000"))
def login(usuario, password):
    try:
        response = requests.post(
            f'{API_URL}/auth/login',
            json={'usuario': usuario, 'password': password}
        )
        # DEBUG - ver respuesta cruda
        st.write(f"Status: {response.status_code}")
        st.write(f"Respuesta: {response.json()}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            st.session_state['token'] = data['access_token']
            st.session_state['user'] = data['user']
            st.session_state['rol'] = data['user']['rol']
            st.session_state['nombre'] = data['user']['nombre']
            return True
        return False
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        st.write(f"Detalle: {str(e)}")
        return False
def logout():
    st.session_state.clear()
    st.rerun()

def mostrar_login():
    st.markdown('<h1 style="text-align: center;">🔐 Iniciar Sesión</h1>', unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True, type="primary"):
                if login(usuario, password):
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas")

def require_auth(roles_permitidos: list = None):
    """Llama esto al inicio de cada página"""
    if 'token' not in st.session_state:
        mostrar_login()
        st.stop()
    
    if roles_permitidos and st.session_state.get('rol') not in roles_permitidos:
        st.error("🚫 No tienes permisos para acceder a esta sección")
        st.stop()
    
    # Sidebar con info del usuario en todas las páginas
    with st.sidebar:
        st.divider()
        st.write(f"👤 **{st.session_state.get('nombre', '')}**")
        st.write(f"🏷️ Rol: `{st.session_state.get('rol', '')}`")
