"""
TICKETERA DE SOPORTE - VISTA ADMIN
Con autenticación automática de Streamlit Cloud
Usa PostgreSQL (misma BD que el usuario)
"""

import streamlit as st
import pandas as pd
import json
import psycopg2
from datetime import datetime
import io

# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Ticketera - Admin",
    layout="wide",
    initial_sidebar_state="expanded"
)

# USUARIOS CON PERMISOS DE ADMIN
ADMIN_USERS = [
    "admin@example.com",
    "andrei@aquanqa.com",
    "supervisor@aquanqa.com",
    "usuario_local",
    "lperez@aquanqa.com"
]

# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================

def get_db_connection():
    """Conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(st.secrets["database_url"])
        return conn
    except KeyError:
        st.error("❌ Error: variable 'database_url' no encontrada en Secrets")
        st.info("Agrega tu URL de Supabase en Settings → Secrets con el nombre 'database_url'")
        st.stop()
    except psycopg2.OperationalError as e:
        st.error(f"❌ Error de conexión a la BD: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error desconocido: {type(e).__name__}: {str(e)}")
        st.stop()

def cargar_tickets():
    """Cargar todos los tickets"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets ORDER BY fecha_creacion DESC')
    columnas = [desc[0] for desc in cursor.description]
    
    tickets = []
    for row in cursor.fetchall():
        ticket = dict(zip(columnas, row))
        ticket['comentarios'] = json.loads(ticket['comentarios'] or '[]')
        tickets.append(ticket)
    
    cursor.close()
    conn.close()
    return tickets

def cambiar_estado_ticket(ticket_id, nuevo_estado):
    """Cambiar estado de un ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE tickets 
        SET estado = %s, fecha_actualizacion = %s
        WHERE id = %s
    ''', (nuevo_estado, datetime.now().strftime('%d/%m/%Y %H:%M:%S'), ticket_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def agregar_comentario(ticket_id, usuario, comentario):
    """Agregar comentario a un ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT comentarios FROM tickets WHERE id = %s', (ticket_id,))
    resultado = cursor.fetchone()
    comentarios = json.loads(resultado[0] or '[]') if resultado else []
    
    comentarios.append({
        'usuario': usuario,
        'texto': comentario,
        'fecha': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })
    
    cursor.execute('''
        UPDATE tickets 
        SET comentarios = %s, fecha_actualizacion = %s
        WHERE id = %s
    ''', (json.dumps(comentarios), datetime.now().strftime('%d/%m/%Y %H:%M:%S'), ticket_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_ticket(ticket_id):
    """Eliminar un ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tickets WHERE id = %s', (ticket_id,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_archivo(ticket_id):
    """Obtener archivo de un ticket"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT archivo_binario, nombre_archivo FROM tickets WHERE id = %s', (ticket_id,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if resultado:
        archivo_binario, nombre_archivo = resultado
        # Convertir memoryview a bytes si es necesario
        if isinstance(archivo_binario, memoryview):
            archivo_binario = bytes(archivo_binario)
        return archivo_binario, nombre_archivo
    return None, None

# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def obtener_usuario_streamlit():
    """Obtener email del usuario invitado en Streamlit Cloud"""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        
        if ctx and hasattr(ctx, 'user_info') and ctx.user_info:
            if hasattr(ctx.user_info, 'email'):
                email = ctx.user_info.email
                if email and email != "unknown":
                    return email
    except:
        pass
    
    if 'admin_login_user' in st.session_state:
        return st.session_state.admin_login_user
    
    return None

def mostrar_login_desarrollo():
    """Mostrar login para desarrollo local"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 style="text-align: center;">⚙️ PANEL ADMINISTRADOR</h1>', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center;">Desarrollo Local - Login</h3>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.info("💡 Estás en desarrollo local. Selecciona un usuario admin.")
        
        usuario_seleccionado = st.selectbox(
            "Selecciona usuario admin:",
            ADMIN_USERS
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
        {chr(10).join([f"- {u}" for u in ADMIN_USERS])}
        
        Si deberías tener acceso, contacta con el administrador.
        """)

# ============================================================
# VISTA ADMIN
# ============================================================

def vista_admin(username):
    """Vista principal del administrador"""
    
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        st.title("⚙️ PANEL ADMINISTRADOR")
    
    with col3:
        st.write(f"👤 **{username}**")
    
    st.markdown("Gestión de Tickets de Soporte")
    st.divider()
    
    tickets = cargar_tickets()
    
    # DASHBOARD
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
    
    # FILTROS
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
    
    if ordenar_por == "Más recientes":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['fecha_creacion'], reverse=True)
    elif ordenar_por == "Más antiguos":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['fecha_creacion'])
    elif ordenar_por == "Más registros":
        tickets_filtrados = sorted(tickets_filtrados, key=lambda x: x['cantidad_registros'], reverse=True)
    
    st.divider()
    
    # TABLA DE TICKETS
    if not tickets_filtrados:
        st.info("📭 No hay tickets con estos filtros")
    else:
        st.subheader(f"📋 Tickets ({len(tickets_filtrados)})")
        
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
        
        # DETALLES DE TICKETS
        st.subheader("🎫 Detalles de Tickets")
        
        for ticket in tickets_filtrados:
            if ticket['estado'] == 'Abierto':
                color = '🔴'
            elif ticket['estado'] == 'En Progreso':
                color = '🟡'
            else:
                color = '🟢'
            
            with st.expander(f"{color} [{ticket['id']}] {ticket['titulo']}"):
                
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
                
                st.write("**Descripción:**")
                st.write(ticket['descripcion'])
                
                st.divider()
                
                # Archivo
                st.write("**📎 Archivo Adjunto:**")
                archivo_binario, nombre_archivo = obtener_archivo(ticket['id'])
                
                if archivo_binario and nombre_archivo:
                    col1, col2 = st.columns([0.7, 0.3])
                    with col1:
                        st.write(f"📁 `{nombre_archivo}`")
                    with col2:
                        st.download_button(
                            label="📥 Descargar",
                            data=archivo_binario,
                            file_name=nombre_archivo,
                            key=f"download_{ticket['id']}"
                        )
                    
                    st.write("**📊 Vista previa de datos:**")
                    try:
                        df_datos = pd.read_excel(io.BytesIO(archivo_binario))
                        st.dataframe(df_datos, use_container_width=True, height=300)
                        
                        csv = df_datos.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📊 Descargar como CSV",
                            data=csv,
                            file_name=f"{ticket['id']}_datos.csv",
                            mime="text/csv",
                            key=f"csv_{ticket['id']}"
                        )
                    except Exception as e:
                        st.error(f"Error al leer archivo: {str(e)}")
                
                st.divider()
                
                # Comentarios
                st.write("**💬 Comentarios:**")
                
                if ticket['comentarios']:
                    for com in ticket['comentarios']:
                        st.write(f"👤 **{com['usuario']}** _{com['fecha']}_")
                        st.write(f"> {com['texto']}")
                else:
                    st.info("Sin comentarios")
                
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
                
                # Acciones administrativas
                st.write("**⚠️ Acciones Administrativas**")
                col1, col2 = st.columns([0.7, 0.3])
                
                with col2:
                    if st.button("🗑️ Eliminar Ticket", key=f"delete_{ticket['id']}", type="secondary"):
                        eliminar_ticket(ticket['id'])
                        st.warning("✅ Ticket eliminado")
                        st.rerun()
    
    st.divider()
    
    # EXPORTACIÓN
    st.subheader("📊 Exportación de Datos")
    
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
    
    username = obtener_usuario_streamlit()
    
    if username is None:
        mostrar_login_desarrollo()
        return
    
    if not es_admin(username):
        mostrar_acceso_denegado(username)
    else:
        vista_admin(username)

if __name__ == "__main__":
    main()