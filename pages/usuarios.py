import streamlit as st
import requests
from auth import require_auth
import os

require_auth(roles_permitidos=['ADMIN'])

import os
import streamlit as st

API_URL = st.secrets.get("API_URL", os.getenv("API_URL", "http://localhost:3000"))
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}

st.title("👥 Maestro de Usuarios")
st.divider()

tab1, tab2 = st.tabs(["📋 Lista de Usuarios", "➕ Crear Usuario"])

with tab1:
    st.subheader("📋 Usuarios del Sistema")

    try:
        response = requests.get(f"{API_URL}/users", headers=get_headers())
        if response.status_code == 200:
            usuarios = response.json()

            if not usuarios:
                st.info("No hay usuarios registrados")
            else:
                for user in usuarios:
                    color = '🟢' if user['activo'] else '🔴'
                    with st.expander(f"{color} {user['nombre']} | {user['usuario']} | `{user['rol']}`"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**ID:** {user['id']}")
                            st.write(f"**Nombre:** {user['nombre']}")
                        with col2:
                            st.write(f"**Usuario:** {user['usuario']}")
                            st.write(f"**Rol:** {user['rol']}")
                        with col3:
                            st.write(f"**Activo:** {'✅' if user['activo'] else '❌'}")

                        st.divider()
                        col1, col2 = st.columns(2)

                        with col1:
                            nuevo_rol = st.selectbox(
                                "Cambiar Rol:",
                                ["ADMIN", "SUPERVISOR", "USER"],
                                index=["ADMIN", "SUPERVISOR", "USER"].index(user['rol']),
                                key=f"rol_{user['id']}"
                            )
                            nuevo_activo = st.checkbox("Activo", value=user['activo'], key=f"activo_{user['id']}")

                            if st.button("💾 Actualizar", key=f"update_{user['id']}"):
                                r = requests.put(
                                    f"{API_URL}/users/{user['id']}",
                                    json={"rol": nuevo_rol, "activo": nuevo_activo},
                                    headers=get_headers()
                                )
                                if r.status_code == 200:
                                    st.success("✅ Usuario actualizado")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al actualizar")

                        with col2:
                            nueva_password = st.text_input("Nueva Contraseña:", type="password", key=f"pass_{user['id']}")
                            if st.button("🔑 Cambiar Password", key=f"pass_btn_{user['id']}"):
                                if nueva_password:
                                    r = requests.put(
                                        f"{API_URL}/users/{user['id']}",
                                        json={"password": nueva_password},
                                        headers=get_headers()
                                    )
                                    if r.status_code == 200:
                                        st.success("✅ Password actualizado")
                                    else:
                                        st.error("❌ Error al actualizar")
                                else:
                                    st.warning("Ingresa una contraseña")

                        st.divider()
                        if st.button("🗑️ Eliminar Usuario", key=f"delete_{user['id']}", type="secondary"):
                            r = requests.delete(f"{API_URL}/users/{user['id']}", headers=get_headers())
                            if r.status_code == 200:
                                st.success("✅ Usuario eliminado")
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar")
        else:
            st.error("❌ Error al cargar usuarios")
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

with tab2:
    st.subheader("➕ Crear Nuevo Usuario")

    with st.form("form_crear_usuario"):
        nombre = st.text_input("Nombre completo:")
        usuario = st.text_input("Usuario (login):")
        email = st.text_input("Email:")
        password = st.text_input("Contraseña:", type="password")
        rol = st.selectbox("Rol:", ["USER", "SUPERVISOR", "ADMIN"])

        if st.form_submit_button("✅ Crear Usuario", type="primary"):
            if not nombre or not usuario or not password or not email:
                st.error("❌ Todos los campos son obligatorios")
            else:
                try:
                    r = requests.post(
                        f"{API_URL}/users",
                        json={"nombre": nombre, "usuario": usuario, "password": password, "email": email, "rol": rol},
                        headers=get_headers()
                    )
                    if r.status_code in [200, 201]:
                        st.success(f"✅ Usuario '{usuario}' creado exitosamente")
                        st.rerun()
                    else:
                        error = r.json().get('message', 'Error desconocido')
                        st.error(f"❌ {error}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")