import streamlit as st

rol = st.session_state.get('rol', '')
nombre = st.session_state.get('nombre', '')

st.title("🏠 Bienvenido al Sistema")
st.write(f"👤 **{nombre}** | 🏷️ Rol: `{rol}`")
st.divider()

if rol == 'ADMIN':
    st.info("✅ Tienes acceso completo al sistema")
elif rol == 'SUPERVISOR':
    st.info("✅ Tienes acceso a: Comparativa Horas, Indicadores, Ticketera")
elif rol == 'USER':
    st.info("✅ Tienes acceso a: Ticketera")