import streamlit as st
from auth import require_auth

st.set_page_config(
    page_title="Sistema RRHH",
    layout="wide",
    initial_sidebar_state="expanded"
)

require_auth()

rol = st.session_state.get('rol', '')

# Páginas base
pagina_home = st.Page("pages/home.py", title="Inicio", icon="🏠")
pagina_admin = st.Page("pages/admin.py", title="Admin Tickets", icon="⚙️")
pagina_comparativa = st.Page("pages/comparativa_horas.py", title="Comparativa Horas", icon="📊")
pagina_indicadores = st.Page("pages/indicadores_soporte.py", title="Indicadores", icon="📈")
pagina_ticketera = st.Page("pages/ticketera_user.py", title="Ticketera", icon="🎫")
pagina_usuarios = st.Page("pages/usuarios.py", title="Usuarios", icon="👥")
# Mostrar páginas según rol
if rol == 'ADMIN':
    paginas = [pagina_home, pagina_admin, pagina_comparativa, pagina_indicadores, pagina_ticketera, pagina_usuarios]
elif rol == 'SUPERVISOR':
    paginas = [pagina_home, pagina_comparativa, pagina_indicadores, pagina_ticketera]
elif rol == 'USER':
    paginas = [pagina_home, pagina_ticketera]
else:
    paginas = [pagina_home]

pg = st.navigation(paginas)
pg.run()