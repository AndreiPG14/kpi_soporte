import streamlit as st
import pandas as pd
import json
import psycopg2
import requests
from datetime import datetime
import io
from auth import require_auth

API_URL = "https://backend-ticket-si99.onrender.com"

require_auth(roles_permitidos=['ADMIN'])

# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================

def get_db_connection():
    try:
        conn = psycopg2.connect(st.secrets["database_url"])
        return conn
    except KeyError:
        st.error("❌ Error: variable 'database_url' no encontrada en Secrets")
        st.stop()
    except psycopg2.OperationalError as e:
        st.error(f"❌ Error de conexión a la BD: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error desconocido: {type(e).__name__}: {str(e)}")
        st.stop()

def cargar_tickets():
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

def cambiar_estado_ticket(ticket_id, nuevo_estado, titulo):
    try:
        requests.put(
            f"{API_URL}/tickets/{ticket_id}/estado",
            json={"estado": nuevo_estado, "titulo": titulo},
            headers={"Authorization": f"Bearer {st.session_state.get('token', '')}"}
        )
    except Exception as e:
        st.error(f"Error notificando: {e}")
    
    # Igual actualiza directo en BD
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tickets SET estado = %s, fecha_actualizacion = %s WHERE id = %s
    ''', (nuevo_estado, datetime.now().strftime('%d/%m/%Y %H:%M:%S'), ticket_id))
    conn.commit()
    cursor.close()
    conn.close()
def agregar_comentario(ticket_id, usuario, comentario):
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tickets WHERE id = %s', (ticket_id,))
    conn.commit()
    cursor.close()
    conn.close()

def obtener_archivo(ticket_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT archivo_binario, nombre_archivo FROM tickets WHERE id = %s', (ticket_id,))
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    if resultado:
        archivo_binario, nombre_archivo = resultado
        if isinstance(archivo_binario, memoryview):
            archivo_binario = bytes(archivo_binario)
        return archivo_binario, nombre_archivo
    return None, None

# ============================================================
# VISTA ADMIN
# ============================================================

def vista_admin():
    username = st.session_state.get('user', {}).get('usuario', '')

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
        st.metric("🔴 Abiertos", len([t for t in tickets if t['estado'] == 'Abierto']))
    with col3:
        st.metric("🟡 En Progreso", len([t for t in tickets if t['estado'] == 'En Progreso']))
    with col4:
        st.metric("🟢 Cerrados", len([t for t in tickets if t['estado'] == 'Cerrado']))
    with col5:
        st.metric("👥 Usuarios", len(set([t['usuario'] for t in tickets])))

    st.divider()

    # FILTROS
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_estado = st.selectbox("Filtrar por estado:", ["Todos", "Abierto", "En Progreso", "Cerrado"])
    with col2:
        usuarios_list = sorted(list(set([t['usuario'] for t in tickets])))
        filtro_usuario = st.selectbox("Filtrar por usuario:", ["Todos"] + usuarios_list)
    with col3:
        ordenar_por = st.selectbox("Ordenar por:", ["Más recientes", "Más antiguos", "Más registros"])

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

    if not tickets_filtrados:
        st.info("📭 No hay tickets con estos filtros")
    else:
        st.subheader(f"📋 Tickets ({len(tickets_filtrados)})")

        df_display = pd.DataFrame([{
            'ID': t['id'],
            'Título': t['titulo'][:50],
            'Usuario': t['usuario'],
            'Estado': t['estado'],
            'Registros': t['cantidad_registros'],
            'Creado': t['fecha_creacion'],
            'Actualizado': t['fecha_actualizacion']
        } for t in tickets_filtrados])
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("🎫 Detalles de Tickets")

        for ticket in tickets_filtrados:
            color = '🔴' if ticket['estado'] == 'Abierto' else '🟡' if ticket['estado'] == 'En Progreso' else '🟢'

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
                            cambiar_estado_ticket(ticket['id'], nuevo_estado, ticket['titulo'])
                            st.success("✅ Estado actualizado")
                            st.rerun()
                st.divider()
                st.write("**Descripción:**")
                st.write(ticket['descripcion'])
                st.divider()

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
                st.write("**💬 Comentarios:**")
                if ticket['comentarios']:
                    for com in ticket['comentarios']:
                        st.write(f"👤 **{com['usuario']}** _{com['fecha']}_")
                        st.write(f"> {com['texto']}")
                else:
                    st.info("Sin comentarios")

                nuevo_comentario = st.text_area("Agregar comentario:", key=f"comentario_{ticket['id']}", height=80)
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
                st.write("**⚠️ Acciones Administrativas**")
                col1, col2 = st.columns([0.7, 0.3])
                with col2:
                    if st.button("🗑️ Eliminar Ticket", key=f"delete_{ticket['id']}", type="secondary"):
                        eliminar_ticket(ticket['id'])
                        st.warning("✅ Ticket eliminado")
                        st.rerun()

    st.divider()
    st.subheader("📊 Exportación de Datos")
    if st.button("📥 Exportar Tickets a CSV", use_container_width=True):
        df_export = pd.DataFrame([{
            'ID': t['id'],
            'Título': t['titulo'],
            'Usuario': t['usuario'],
            'Estado': t['estado'],
            'Registros': t['cantidad_registros'],
            'Creado': t['fecha_creacion'],
            'Actualizado': t['fecha_actualizacion']
        } for t in tickets])
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

vista_admin()