"""
TICKETERA DE SOPORTE - VISTA ADMIN
Con autenticación automática de Streamlit Cloud
Solo ciertas cuentas tienen permisos de admin
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Ticketera - Admin",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Archivo para almacenar tickets
TICKETS_FILE = "tickets_data.json"
UPLOADS_DIR = "ticket_uploads"

# Crear directorio de uploads si no existe
Path(UPLOADS_DIR).mkdir(exist_ok=True)

# USUARIOS CON PERMISOS DE ADMIN (actualizar con tus cuentas)
ADMIN_USERS = [
    "admin@example.com",
    "andrei@aquanqa.com",
    "supervisor@aquanqa.com"
]

# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def obtener_usuario_streamlit():
    """
    Obtener usuario automáticamente de Streamlit Cloud
    En desarrollo local: pedir login manualmente
    En Streamlit Cloud: obtiene del contexto
    """
    try:
        # En Streamlit Cloud, el usuario está disponible aquí
        from streamlit.connections import _get_session
        session = _get_session()
        
        if hasattr(session, '_user_id'):
            return session._user_id
    except:
        pass
    
    # Alternativa: obtener del contexto de Streamlit
    try:
        if 'user' in st.session_state:
            return st.session_state.user
    except:
        pass
    
    # En desarrollo local, usar valor de session_state si existe
    if 'admin_login_user' in st.session_state:
        return st.session_state.admin_login_user
    
    # Si no hay usuario, retornar None para mostrar login
    return None

def mostrar_login_desarrollo():
    """Mostrar login para desarrollo local"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 style="text-align: center;">⚙️ PANEL ADMINISTRADOR</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center;">Desarrollo Local - Login</h3>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.info("💡 Estás en desarrollo local. Selecciona un usuario admin para testing.")
        
        usuario_seleccionado = st.selectbox(
            "Selecciona usuario admin:",
            [
                "andreipg2314@gmail.com",
                "andrei@aquanqa.com",
                "supervisor@aquanqa.com"
            ]
        )
        
        if st.button("✅ Ingresar como Admin", type="primary", use_container_width=True):
            st.session_state.admin_login_user = usuario_seleccionado
            st.success(f"✅ Entrando como {usuario_seleccionado}")
            st.rerun()
        
        st.divider()
        st.caption("🔐 En Streamlit Cloud, se obtiene automáticamente del usuario logueado")

def es_admin(username):
    """Verificar si el usuario tiene permisos de admin"""
    return username.lower() in [u.lower() for u in ADMIN_USERS]

def cargar_tickets():
    """Cargar tickets desde archivo JSON"""
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, 'r') as f:
            return json.load(f)
    return []

def guardar_tickets(tickets):
    """Guardar tickets en archivo JSON"""
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2, ensure_ascii=False)

def cambiar_estado_ticket(ticket_id, nuevo_estado):
    """Cambiar estado de un ticket"""
    tickets = cargar_tickets()
    
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['estado'] = nuevo_estado
            ticket['fecha_actualizacion'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            break
    
    guardar_tickets(tickets)

def agregar_comentario(ticket_id, usuario, comentario):
    """Agregar comentario a un ticket"""
    tickets = cargar_tickets()
    
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            ticket['comentarios'].append({
                'usuario': usuario,
                'texto': comentario,
                'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
            ticket['fecha_actualizacion'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            break
    
    guardar_tickets(tickets)

def eliminar_ticket(ticket_id):
    """Eliminar un ticket y su archivo"""
    tickets = cargar_tickets()
    
    # Encontrar y eliminar el archivo
    for ticket in tickets:
        if ticket['id'] == ticket_id:
            archivo_ruta = os.path.join(UPLOADS_DIR, ticket['archivo'])
            if os.path.exists(archivo_ruta):
                os.remove(archivo_ruta)
            break
    
    # Eliminar ticket
    tickets = [t for t in tickets if t['id'] != ticket_id]
    guardar_tickets(tickets)

def leer_archivo_excel(ticket_id, archivo_nombre):
    """Leer archivo Excel de un ticket"""
    try:
        archivo_ruta = os.path.join(UPLOADS_DIR, archivo_nombre)
        if os.path.exists(archivo_ruta):
            return pd.read_excel(archivo_ruta)
    except Exception as e:
        st.error(f"Error al leer archivo: {str(e)}")
    return None

# ============================================================
# VISTA RESTRINGIDA
# ============================================================

def mostrar_acceso_denegado(username):
    """Mostrar página de acceso denegado"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 style="text-align: center;">🔒 ACCESO DENEGADO</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.error(f"❌ Tu usuario '{username}' no tiene permisos de administrador")
        st.info(f"""
        **Tu usuario:** {username}
        
        **Usuarios con acceso admin:**
        - admin@example.com
        - andrei@aquanqa.com
        - supervisor@aquanqa.com
        
        Si deberías tener acceso, contacta con el administrador.
        """)

# ============================================================
# VISTA ADMIN
# ============================================================

def vista_admin(username):
    """Vista principal del administrador"""
    
    # Header
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        st.title("⚙️ PANEL ADMINISTRADOR")
    
    with col3:
        st.write(f"👤 **{username}**")
    
    st.markdown("Gestión de Tickets de Soporte")
    st.divider()
    
    # Cargar tickets
    tickets = cargar_tickets()
    
    # ============================================================
    # DASHBOARD
    # ============================================================
    
    st.subheader("📊 Dashboard")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📋 Total", len(tickets))
    
    with col2:
        abiertos = len([t for t in tickets if t['estado'] == 'Abierto'])
        st.metric("🔴 Abiertos", abiertos)
    
    with col3:
        en_progreso = len([t for t in tickets if t['estado'] == 'En Progreso'])
        st.metric("🟡 En Progreso", en_progreso)
    
    with col4:
        cerrados = len([t for t in tickets if t['estado'] == 'Cerrado'])
        st.metric("🟢 Cerrados", cerrados)
    
    with col5:
        usuarios = len(set([t['usuario'] for t in tickets]))
        st.metric("👥 Usuarios", usuarios)
    
    st.divider()
    
    # ============================================================
    # FILTROS
    # ============================================================
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_estado = st.selectbox(
            "Filtrar por estado:",
            ["Todos", "Abierto", "En Progreso", "Cerrado"]
        )
    
    with col2:
        usuarios_list = sorted(list(set([t['usuario'] for t in tickets])))
        filtro_usuario = st.selectbox(
            "Filtrar por usuario:",
            ["Todos"] + usuarios_list
        )
    
    with col3:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            ["Más recientes", "Más antiguos", "Más registros"]
        )
    
    # Aplicar filtros
    tickets_filtrados = tickets
    
    if filtro_estado != "Todos":
        tickets_filtrados = [t for t in tickets_filtrados if t['estado'] == filtro_estado]
    
    if filtro_usuario != "Todos":
        tickets_filtrados = [t for t in tickets_filtrados if t['usuario'] == filtro_usuario]
    
    # Aplicar ordenamiento
    if ordenar_por == "Más recientes":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['fecha_creacion'], reverse=True)
    elif ordenar_por == "Más antiguos":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['fecha_creacion'])
    elif ordenar_por == "Más registros":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['cantidad_registros'], reverse=True)
    
    st.divider()
    
    # ============================================================
    # TABLA DE TICKETS
    # ============================================================
    
    if not tickets_filtrados:
        st.info("📭 No hay tickets con estos filtros")
    else:
        st.subheader(f"📋 Tickets ({len(tickets_filtrados)})")
        
        # Crear dataframe para la tabla
        df_display = pd.DataFrame([
            {
                'ID': t['id'],
                'Título': t['titulo'][:50],
                'Usuario': t['usuario'],
                'Estado': t['estado'],
                'Registros': t['cantidad_registros'],
                'Creado': t['fecha_creacion'],
                'Actualizado': t['fecha_actualizacion']
            }
            for t in tickets_filtrados
        ])
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # ============================================================
        # DETALLES DE TICKETS
        # ============================================================
        
        st.subheader("🎫 Detalles de Tickets")
        
        for idx, ticket in enumerate(tickets_filtrados):
            # Color según estado
            if ticket['estado'] == 'Abierto':
                color = '🔴'
            elif ticket['estado'] == 'En Progreso':
                color = '🟡'
            else:
                color = '🟢'
            
            with st.expander(f"{color} [{ticket['id']}] {ticket['titulo']}", expanded=False):
                
                # Información general
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Información General**")
                    st.write(f"**ID:** {ticket['id']}")
                    st.write(f"**Usuario:** {ticket['usuario']}")
                    st.write(f"**Registros:** {ticket['cantidad_registros']}")
                
                with col2:
                    st.write("**Fechas**")
                    st.write(f"**Creado:** {ticket['fecha_creacion']}")
                    st.write(f"**Actualizado:** {ticket['fecha_actualizacion']}")
                    st.write("")
                
                with col3:
                    st.write("**Cambiar Estado**")
                    nuevo_estado = st.selectbox(
                        "Estado:",
                        ["Abierto", "En Progreso", "Cerrado"],
                        index=["Abierto", "En Progreso", "Cerrado"].index(ticket['estado']),
                        key=f"estado_{ticket['id']}"
                    )
                    
                    if nuevo_estado != ticket['estado']:
                        if st.button("✅ Actualizar", key=f"btn_update_{ticket['id']}"):
                            cambiar_estado_ticket(ticket['id'], nuevo_estado)
                            st.success("✅ Estado actualizado")
                            st.rerun()
                
                st.divider()
                
                # Descripción
                st.write("**Descripción:**")
                st.write(ticket['descripcion'])
                
                st.divider()
                
                # Archivo
                st.write("**📎 Archivo Adjunto:**")
                archivo_ruta = os.path.join(UPLOADS_DIR, ticket['archivo'])
                
                if os.path.exists(archivo_ruta):
                    col1, col2 = st.columns([0.7, 0.3])
                    
                    with col1:
                        st.write(f"Archivo: `{ticket['archivo'].split('_', 1)[1]}`")
                    
                    with col2:
                        with open(archivo_ruta, 'rb') as f:
                            st.download_button(
                                label="📥 Descargar",
                                data=f.read(),
                                file_name=ticket['archivo'].split('_', 1)[1],
                                key=f"download_{ticket['id']}"
                            )
                    
                    # Preview de datos
                    st.write("**📊 Vista previa de datos:**")
                    df_datos = leer_archivo_excel(ticket['id'], ticket['archivo'])
                    
                    if df_datos is not None:
                        st.dataframe(df_datos, use_container_width=True, height=300)
                        
                        # Opción para descargar datos procesados
                        col1, col2 = st.columns(2)
                        with col1:
                            csv = df_datos.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📊 Descargar como CSV",
                                data=csv,
                                file_name=f"{ticket['id']}_datos.csv",
                                mime="text/csv",
                                key=f"csv_{ticket['id']}"
                            )
                
                st.divider()
                
                # Comentarios
                st.write("**💬 Comentarios:**")
                
                if ticket['comentarios']:
                    for com in ticket['comentarios']:
                        st.write(f"👤 **{com['usuario']}** _{com['fecha']}_")
                        st.write(f"> {com['texto']}")
                        st.write("")
                else:
                    st.info("Sin comentarios")
                
                # Agregar comentario
                nuevo_comentario = st.text_area(
                    "Agregar comentario:",
                    key=f"comentario_{ticket['id']}",
                    height=80
                )
                
                col1, col2 = st.columns([0.7, 0.3])
                with col2:
                    if st.button("💬 Enviar", key=f"btn_comentario_{ticket['id']}"):
                        if nuevo_comentario.strip():
                            agregar_comentario(ticket['id'], username, nuevo_comentario)
                            st.success("✅ Comentario agregado")
                            st.rerun()
                        else:
                            st.warning("Escribe un comentario")
                
                st.divider()
                
                # Acciones peligrosas
                st.write("**⚠️ Acciones Administrativas**")
                col1, col2 = st.columns([0.7, 0.3])
                
                with col2:
                    if st.button("🗑️ Eliminar Ticket", key=f"delete_{ticket['id']}", type="secondary"):
                        eliminar_ticket(ticket['id'])
                        st.warning("✅ Ticket eliminado")
                        st.rerun()
    
    st.divider()
    
    # ============================================================
    # EXPORTACIÓN
    # ============================================================
    
    st.subheader("📊 Exportación de Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Tickets a CSV", use_container_width=True):
            df_export = pd.DataFrame([
                {
                    'ID': t['id'],
                    'Título': t['titulo'],
                    'Usuario': t['usuario'],
                    'Estado': t['estado'],
                    'Registros': t['cantidad_registros'],
                    'Creado': t['fecha_creacion'],
                    'Actualizado': t['fecha_actualizacion']
                }
                for t in tickets
            ])
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"tickets_{datetime.now().strftime('%d_%m_%Y')}.csv",
                mime="text/csv"
            )

# ============================================================
# MAIN
# ============================================================

def main():
    """Función principal"""
    
    # Obtener usuario automáticamente
    username = obtener_usuario_streamlit()
    
    # Si no hay usuario en desarrollo local, mostrar login
    if username is None:
        mostrar_login_desarrollo()
        return
    
    # Verificar permisos
    if not es_admin(username):
        mostrar_acceso_denegado(username)
    else:
        vista_admin(username)

if __name__ == "__main__":
    main()