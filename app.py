import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np

def calcular_indicadores(df):
    # Total de modificaciones
    total_modificaciones = df['CANTIDAD MODIFICADA'].sum()
    
    # Promedio de modificaciones
    promedio_modificaciones = df['CANTIDAD MODIFICADA'].mean()
    
    # Máximo de modificaciones en un registro
    max_modificaciones = df['CANTIDAD MODIFICADA'].max()
    
    # Desviación estándar de modificaciones
    std_modificaciones = df['CANTIDAD MODIFICADA'].std()
    
    # Mediana
    mediana_modificaciones = df['CANTIDAD MODIFICADA'].median()
    
    # Coeficiente de variación
    coef_variacion = (std_modificaciones / promedio_modificaciones * 100) if promedio_modificaciones > 0 else 0
    
    return {
        'Total Modificaciones': total_modificaciones,
        'Promedio Modificaciones': round(promedio_modificaciones, 2),
        'Máximo Modificaciones': max_modificaciones,
        'Variabilidad Modificaciones': round(std_modificaciones, 2),
        'Mediana': round(mediana_modificaciones, 2),
        'Coef Variación': round(coef_variacion, 2)
    }

def generar_analisis_cuantitativo(df_filtrado, indicadores):
    """Genera análisis textual de indicadores cuantitativos"""
    total = indicadores['Total Modificaciones']
    promedio = indicadores['Promedio Modificaciones']
    maximo = indicadores['Máximo Modificaciones']
    variabilidad = indicadores['Variabilidad Modificaciones']
    mediana = indicadores['Mediana']
    coef_var = indicadores['Coef Variación']
    
    analisis = f"""
    **ANÁLISIS CUANTITATIVO - RESUMEN EJECUTIVO**
    
    Con un total de **{total:,.0f} modificaciones** registradas en el período seleccionado, se observa una 
    distribución de cambios con un promedio de **{promedio:.2f} modificaciones por registro**.
    
    **Hallazgos Clave:**
    
    1. **Dispersión de Datos (Variabilidad: {variabilidad:.2f})**
       - El coeficiente de variación es {coef_var:.2f}%, indicando {'alta' if coef_var > 50 else 'moderada' if coef_var > 25 else 'baja'} variabilidad
       - La diferencia entre la mediana ({mediana:.2f}) y el promedio ({promedio:.2f}) {'es significativa, sugiriendo outliers' if abs(mediana - promedio) > variabilidad else 'es normal'}
       - Hay registros con hasta {maximo:,.0f} modificaciones, {'lo que representa anomalías significativas' if maximo > promedio + 2*variabilidad else 'dentro del rango esperado'}
    
    2. **Distribución de Incidencias**
       - {f"El {(df_filtrado['CANTIDAD MODIFICADA'] == maximo).sum()} registro(s) contiene(n) el máximo de modificaciones" if (df_filtrado['CANTIDAD MODIFICADA'] == maximo).sum() > 0 else 'Datos distribuidos'}
       - {'Existe una concentración alta de errores en pocos registros' if coef_var > 80 else 'Los errores están distribuidos relativamente de forma uniforme' if coef_var < 30 else 'Distribución moderada de errores'}
    
    **Interpretación:** {'Se requiere investigación inmediata de registros con alta cantidad de modificaciones' if coef_var > 50 else 'La variabilidad es controlada, pero se deben monitorear los picos'}
    """
    return analisis

def generar_analisis_temporal(df_filtrado):
    """Genera análisis de tendencias temporales"""
    modificaciones_por_semana = df_filtrado.groupby('SEMANA')['CANTIDAD MODIFICADA'].sum()
    
    if len(modificaciones_por_semana) < 2:
        return "No hay suficientes datos para análisis temporal."
    
    primera_semana = modificaciones_por_semana.iloc[0]
    ultima_semana = modificaciones_por_semana.iloc[-1]
    cambio_porcentual = ((ultima_semana - primera_semana) / primera_semana) * 100
    
    semana_max = modificaciones_por_semana.idxmax()
    semana_min = modificaciones_por_semana.idxmin()
    
    # Calcular promedio y tendencia
    promedio_semanal = modificaciones_por_semana.mean()
    semanas_sobre_promedio = (modificaciones_por_semana > promedio_semanal).sum()
    
    analisis = f"""
    **ANÁLISIS TEMPORAL - EVOLUCIÓN DE INCIDENCIAS**
    
    El período analizado muestra una {'mejora' if cambio_porcentual < 0 else 'deterioro'} de {abs(cambio_porcentual):.2f}% 
    desde la semana {modificaciones_por_semana.index[0]} hasta la semana {modificaciones_por_semana.index[-1]}.
    
    **Hallazgos Clave:**
    
    1. **Tendencia General**
       - Primera semana: {primera_semana:,.0f} modificaciones
       - Última semana: {ultima_semana:,.0f} modificaciones
       - Cambio: {'↓' if cambio_porcentual < 0 else '↑'} {abs(cambio_porcentual):.2f}%
       - Promedio semanal: {promedio_semanal:,.0f} modificaciones
    
    2. **Semanas Críticas**
       - Semana con más incidencias: Semana {semana_max} ({modificaciones_por_semana[semana_max]:,.0f} modificaciones)
       - Semana con menos incidencias: Semana {semana_min} ({modificaciones_por_semana[semana_min]:,.0f} modificaciones)
       - Variación entre pico y valle: {((modificaciones_por_semana[semana_max] - modificaciones_por_semana[semana_min]) / modificaciones_por_semana[semana_min] * 100):.2f}%
       - Semanas sobre el promedio: {semanas_sobre_promedio} de {len(modificaciones_por_semana)}
    
    3. **Patrón Observado**
       {'La tendencia es CRECIENTE - Se está perdiendo control de la calidad' if cambio_porcentual > 20 else 'La tendencia es DECRECIENTE - Mejora sostenible en la calidad' if cambio_porcentual < -20 else 'La tendencia es ESTABLE - Se mantiene un nivel consistente'}
    
    **Recomendación:** {'Investigar causas del aumento y tomar acciones correctivas urgentes' if cambio_porcentual > 20 else 'Mantener y potenciar las mejoras implementadas' if cambio_porcentual < -20 else 'Continuar monitoreo cercano para prevenir incrementos'}
    """
    return analisis

def generar_analisis_responsables(df_filtrado):
    """Genera análisis de responsables de incidencias"""
    modificaciones_por_responsable = df_filtrado.groupby('RESPONSABLE DE INCIDENCIA')['CANTIDAD MODIFICADA'].sum()
    top_5 = modificaciones_por_responsable.nlargest(5)
    
    total_modificaciones = modificaciones_por_responsable.sum()
    concentracion_top5 = (top_5.sum() / total_modificaciones) * 100
    
    # Análisis del top 1
    top_1_nombre = top_5.index[0]
    top_1_valor = top_5.iloc[0]
    top_1_porcentaje = (top_1_valor / total_modificaciones) * 100
    
    # Comparación entre responsables
    promedio_responsable = modificaciones_por_responsable.mean()
    responsables_sobre_promedio = (modificaciones_por_responsable > promedio_responsable).sum()
    
    analisis = f"""
    **ANÁLISIS DE RESPONSABLES - GESTIÓN DE INCIDENCIAS POR PERSONAL**
    
    El análisis revela que **{concentracion_top5:.1f}% de todas las modificaciones** se concentran en solo 5 responsables.
    
    **Hallazgos Clave:**
    
    1. **Concentración de Responsabilidad**
       - Top 5 responsables generan: {top_5.sum():,.0f} de {total_modificaciones:,.0f} modificaciones ({concentracion_top5:.1f}%)
       - Total de responsables: {len(modificaciones_por_responsable)}
       - {'CRÍTICO: Altísima concentración de errores en pocos individuos' if concentracion_top5 > 70 else 'IMPORTANTE: Concentración notable, requiere atención' if concentracion_top5 > 50 else 'NORMAL: Distribución relativamente equilibrada'}
    
    2. **Responsable de Mayor Incidencia**
       - **{top_1_nombre}** lidera con **{top_1_valor:,.0f}** modificaciones ({top_1_porcentaje:.1f}% del total)
       - Esto es {(top_1_valor / promedio_responsable):.1f}x el promedio de responsables
       - {'Requiere intervención inmediata con plan de capacitación' if top_1_porcentaje > 20 else 'Se requiere seguimiento y apoyo'}
    
    3. **Distribución Organizacional**
       - Promedio por responsable: {promedio_responsable:,.0f} modificaciones
       - Responsables sobre el promedio: {responsables_sobre_promedio} de {len(modificaciones_por_responsable)} ({(responsables_sobre_promedio/len(modificaciones_por_responsable)*100):.1f}%)
       - Ratio máximo/promedio: {(modificaciones_por_responsable.max() / promedio_responsable):.1f}x
    
    **Diagnóstico:** {'Los procesos, no el personal, son el problema principal - revisar procedimientos' if concentracion_top5 < 40 else 'Hay un problema significativo de inconsistencia - combinar análisis de procesos y capacitación'}
    
    **Plan de Acción:**
       1. Auditoría detallada de los Top 5 responsables (análisis de tipos de errores)
       2. Sesiones de mentoría y capacitación personalizada
       3. Identificar si hay factores externos (volumen, complejidad, cambios recientes)
       4. Implementar sistema de doble verificación para casos críticos
    """
    return analisis

def generar_analisis_empresas(df_filtrado):
    """Genera análisis por empresa"""
    modificaciones_por_empresa = df_filtrado.groupby('EMPRESA')['CANTIDAD MODIFICADA'].sum()
    
    total_modificaciones = modificaciones_por_empresa.sum()
    empresa_mayor = modificaciones_por_empresa.idxmax()
    valor_mayor = modificaciones_por_empresa.max()
    porcentaje_mayor = (valor_mayor / total_modificaciones) * 100
    
    promedio_empresa = modificaciones_por_empresa.mean()
    empresas_sobre_promedio = (modificaciones_por_empresa > promedio_empresa).sum()
    
    # Calcular concentración (índice Herfindahl)
    participaciones = modificaciones_por_empresa / total_modificaciones
    herfindahl = (participaciones ** 2).sum()
    
    analisis = f"""
    **ANÁLISIS POR EMPRESA - DESEMPEÑO COMPARATIVO**
    
    Se identifican **{len(modificaciones_por_empresa)} empresas** con diferentes niveles de desempeño en control de calidad.
    
    **Hallazgos Clave:**
    
    1. **Distribución Inter-empresarial**
       - Empresa con mayor incidencia: **{empresa_mayor}** ({valor_mayor:,.0f} modificaciones, {porcentaje_mayor:.1f}%)
       - Empresa con menor incidencia: **{modificaciones_por_empresa.idxmin()}** ({modificaciones_por_empresa.min():,.0f} modificaciones)
       - Promedio por empresa: {promedio_empresa:,.0f} modificaciones
       - {'Altamente desbalanceado - una empresa domina claramente' if porcentaje_mayor > 50 else 'Moderadamente distribuido' if porcentaje_mayor < 30 else 'Relativamente equilibrado con dominancia moderada'}
    
    2. **Análisis de Concentración (Herfindahl Index)**
       - Índice: {herfindahl:.4f}
       - Interpretación: {'Mercado altamente concentrado - requiere intervención estratégica' if herfindahl > 0.25 else 'Distribución moderada - hay oportunidad de mejora' if herfindahl > 0.15 else 'Distribución equilibrada'}
    
    3. **Empresas Problemáticas**
       - Sobre el promedio: {empresas_sobre_promedio} de {len(modificaciones_por_empresa)}
       - Diferencia máx/mín: {(modificaciones_por_empresa.max() / modificaciones_por_empresa.min() if modificaciones_por_empresa.min() > 0 else 0):.1f}x
    
    **Diagnóstico:** {'Problema sistémico en una sola empresa - requiere auditoría profunda' if porcentaje_mayor > 50 else 'Problemas distribuidos - análisis de procesos cruzados necesario'}
    
    **Recomendaciones por Prioridad:**
       1. URGENTE: Auditoría operativa a {empresa_mayor}
       2. IMPORTANTE: Benchmarking entre empresas para identificar mejores prácticas
       3. PREVENTIVO: Implementar KPIs comparativos entre empresas
       4. ESTRATÉGICO: Considerar compartir soluciones de la empresa con mejor desempeño
    """
    return analisis

def generar_analisis_tipos_incidencia(df_filtrado):
    """Genera análisis de tipos de incidencias"""
    tipos_incidencia = df_filtrado['TIPO INCIDENCIA'].value_counts()
    total = tipos_incidencia.sum()
    tipos_incidencia_pct = tipos_incidencia / total * 100
    
    tipo_mayor = tipos_incidencia.idxmax()
    valor_mayor = tipos_incidencia.max()
    porcentaje_mayor = tipos_incidencia_pct.max()
    
    analisis = f"""
    **ANÁLISIS DE TIPOS DE INCIDENCIA - CAUSAS RAÍZ**
    
    Se documentan **{len(tipos_incidencia)} tipos diferentes** de incidencias en el período.
    
    **Hallazgos Clave:**
    
    1. **Tipo Predominante**
       - Tipo más frecuente: **{tipo_mayor}** ({valor_mayor:,.0f} casos, {porcentaje_mayor:.1f}%)
       - {'Este tipo concentra MÁS del 40% de incidencias - investigar causa raíz' if porcentaje_mayor > 40 else 'Distribución relativamente equilibrada entre tipos'}
    
    2. **Concentración de Incidencias**
       - Top 3 tipos representan: {tipos_incidencia.head(3).sum() / total * 100:.1f}% del total
       - {'Alta concentración en pocos tipos - enfoque en 2-3 problemas clave' if tipos_incidencia.head(3).sum() / total > 0.70 else 'Incidencias variadas - requiere enfoque multi-frente'}
    
    **Recomendación:** Realizar análisis de causa raíz (5 Why's) para {tipo_mayor}, que es el driver principal de errores
    """
    return analisis

def main():
    st.set_page_config(layout="wide", page_title="Dashboard Integral de Indicadores")
    
    st.title("📊 Dashboard Integral de Indicadores - Análisis de Datos")
    st.markdown("**Análisis Profesional de Incidencias y Modificaciones**")
    
    # Cargar archivo
    uploaded_file = st.file_uploader("Cargar Archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Leer archivo
        df = pd.read_excel(uploaded_file)
        
        # Convertir FECHA a datetime
        df['FECHA'] = pd.to_datetime(df['FECHA'])
        
        # Sidebar para filtros
        st.sidebar.header("⚙️ Filtros")
        
        # Obtener semanas únicas
        semanas_unicas = sorted(df['SEMANA'].unique())
        
        # Obtener áreas/fundos únicas
        areas_unicas = sorted(df['ÁREA/FUNDO INVOLUCRADA'].unique())
        
        # Selector de rango de semanas
        semana_inicio = st.sidebar.selectbox(
            "Semana de Inicio", 
            semanas_unicas, 
            index=0
        )
        
        semana_fin = st.sidebar.selectbox(
            "Semana de Fin", 
            semanas_unicas, 
            index=len(semanas_unicas)-1
        )
        
        # Selector de Área/Fundo (multiselect)
        areas_seleccionadas = st.sidebar.multiselect(
            "Seleccionar Áreas/Fundos", 
            areas_unicas, 
            default=areas_unicas
        )
        
        # Filtrar DataFrame por rango de semanas y áreas
        df_filtrado = df[
            (df['SEMANA'] >= semana_inicio) & 
            (df['SEMANA'] <= semana_fin) &
            (df['ÁREA/FUNDO INVOLUCRADA'].isin(areas_seleccionadas))
        ]
        
        # Verificar si hay datos después del filtro
        if df_filtrado.empty:
            st.error("No hay datos que coincidan con los filtros seleccionados.")
            return
        
        # Información general
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"""
        **📈 DATOS CARGADOS**
        - Registros totales: {len(df_filtrado):,}
        - Fecha inicio: {df_filtrado['FECHA'].min().strftime('%d/%m/%Y')}
        - Fecha fin: {df_filtrado['FECHA'].max().strftime('%d/%m/%Y')}
        - Semanas: {semana_inicio} a {semana_fin}
        """)
        
        # ==================== 1. INDICADORES CUANTITATIVOS ====================
        st.header("1️⃣ Indicadores Cuantitativos")
        
        # Cálculo de indicadores
        indicadores = calcular_indicadores(df_filtrado)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Modificaciones", f"{indicadores['Total Modificaciones']:,.0f}")
        with col2:
            st.metric("Promedio", f"{indicadores['Promedio Modificaciones']:.2f}")
        with col3:
            st.metric("Máximo", f"{indicadores['Máximo Modificaciones']:,.0f}")
        with col4:
            st.metric("Variabilidad (σ)", f"{indicadores['Variabilidad Modificaciones']:.2f}")
        
        # Análisis textual
        with st.expander("📋 Análisis Detallado - Indicadores Cuantitativos", expanded=True):
            st.markdown(generar_analisis_cuantitativo(df_filtrado, indicadores))
        
        # ==================== 2. ANÁLISIS TEMPORAL ====================
        st.header("2️⃣ Análisis Temporal - Tendencias")
        
        modificaciones_por_semana = df_filtrado.groupby('SEMANA')['CANTIDAD MODIFICADA'].sum()
        
        # Gráfico de tendencia
        fig_temporal = go.Figure(data=go.Bar(
            x=modificaciones_por_semana.index.astype(str), 
            y=modificaciones_por_semana.values,
            marker_color='rgba(255, 99, 71, 0.7)',
            text=[f'{val:,.0f}' for val in modificaciones_por_semana.values],
            textposition='outside'
        ))
        
        fig_temporal.update_layout(
            title='Evolución de Modificaciones por Semana',
            xaxis_title='Semana',
            yaxis_title='Cantidad de Modificaciones',
            height=500
        )
        
        st.plotly_chart(fig_temporal, use_container_width=True)
        
        # Análisis temporal
        with st.expander("📋 Análisis Detallado - Tendencias Temporales", expanded=True):
            st.markdown(generar_analisis_temporal(df_filtrado))
        
        # ==================== 3. ANÁLISIS POR TIPO DE INCIDENCIA ====================
        st.header("3️⃣ Análisis de Tipos de Incidencia")
        
        col5, col6 = st.columns(2)
        
        with col5:
            tipos_incidencia = df_filtrado['TIPO INCIDENCIA'].value_counts()
            total = tipos_incidencia.sum()
            tipos_incidencia_pct = tipos_incidencia / total * 100
            
            labels = [
                f"{tipo} ({cantidad:,.0f}) - {porcentaje:.1f}%" 
                for tipo, cantidad, porcentaje 
                in zip(tipos_incidencia.index, tipos_incidencia.values, tipos_incidencia_pct.values)
            ]
            
            fig_tipos = go.Figure(data=[go.Pie(
                labels=labels, 
                values=tipos_incidencia.values,
                hole=.3
            )])
            fig_tipos.update_layout(title="Distribución de Incidencias por Tipo")
            st.plotly_chart(fig_tipos, use_container_width=True)
        
        with col6:
            # Gráfico de barras con los tipos
            tipos_sorted = tipos_incidencia.sort_values(ascending=True)
            fig_tipos_barras = go.Figure(go.Bar(
                x=tipos_sorted.values,
                y=tipos_sorted.index,
                orientation='h',
                marker_color='rgba(75, 192, 192, 0.6)',
                text=[f'{val:,.0f}' for val in tipos_sorted.values],
                textposition='outside'
            ))
            fig_tipos_barras.update_layout(
                title="Cantidad de Incidencias por Tipo",
                xaxis_title="Cantidad",
                yaxis_title="Tipo de Incidencia"
            )
            st.plotly_chart(fig_tipos_barras, use_container_width=True)
        
        with st.expander("📋 Análisis Detallado - Tipos de Incidencia"):
            st.markdown(generar_analisis_tipos_incidencia(df_filtrado))
        
        # ==================== 4. ANÁLISIS DE RESPONSABLES ====================
        st.header("4️⃣ Análisis de Responsables - Gestión de Incidencias")
        
        modificaciones_por_responsable = df_filtrado.groupby('RESPONSABLE DE INCIDENCIA')['CANTIDAD MODIFICADA'].sum()
        top_5_responsables = modificaciones_por_responsable.nlargest(5)
        
        col7, col8 = st.columns(2)
        
        with col7:
            total_mod = top_5_responsables.sum()
            porcentajes = (top_5_responsables / total_mod) * 100
            
            fig_responsables = go.Figure(go.Bar(
                x=top_5_responsables.values,
                y=top_5_responsables.index,
                orientation='h',
                marker_color='rgba(255, 99, 71, 0.7)',
                text=[f'{val:,.0f} ({pct:.1f}%)' for val, pct in zip(top_5_responsables.values, porcentajes.values)],
                textposition='outside'
            ))
            
            fig_responsables.update_layout(
                title="Top 5 Responsables con Más Modificaciones",
                xaxis_title="Cantidad",
                yaxis_title="Responsable"
            )
            st.plotly_chart(fig_responsables, use_container_width=True)
        
        with col8:
            labels = [
                f"{resp} ({cant:,.0f}) - {pct:.1f}%" 
                for resp, cant, pct in zip(top_5_responsables.index, top_5_responsables.values, porcentajes.values)
            ]
            
            fig_pie_resp = go.Figure(data=[go.Pie(
                labels=labels, 
                values=top_5_responsables.values,
                hole=.3
            )])
            fig_pie_resp.update_layout(title="Distribución entre Top 5")
            st.plotly_chart(fig_pie_resp, use_container_width=True)
        
        # Tabla detallada de Top 5 con TODAS las categorías (planillas, productividad, jarras)
        st.subheader("📋 Detalle de Top 5 Responsables - Todas las Categorías")
        
        top_5_detalles = []
        for responsable in top_5_responsables.index:
            datos_responsable = df_filtrado[df_filtrado['RESPONSABLE DE INCIDENCIA'] == responsable]
            total_mods = datos_responsable['CANTIDAD MODIFICADA'].sum()
            
            # TIPO más frecuente (planillas, productividad, jarras, etc.)
            tipos_distribucion = datos_responsable['TIPO'].value_counts()
            
            # Construir string con todas las categorías y sus casos
            categorias_texto = " | ".join([
                f"{tipo}: {cantidad} ({(cantidad/len(datos_responsable)*100):.1f}%)"
                for tipo, cantidad in tipos_distribucion.items()
            ])
            
            top_5_detalles.append({
                'Responsable': responsable,
                'Total Modificaciones': int(total_mods),
                'Categorías': categorias_texto,
                '% Total': f'{(total_mods/total_mod*100):.1f}%'
            })
        
        df_top_5_detalles = pd.DataFrame(top_5_detalles)
        st.dataframe(df_top_5_detalles, use_container_width=True, height=300)
        
        # Mostrar vista expandida más detallada
        st.subheader("📊 Vista Expandida - Desglose Completo por Categoría")
        
        for idx, responsable in enumerate(top_5_responsables.index, 1):
            datos_responsable = df_filtrado[df_filtrado['RESPONSABLE DE INCIDENCIA'] == responsable]
            total_mods = datos_responsable['CANTIDAD MODIFICADA'].sum()
            tipos_distribucion = datos_responsable['TIPO'].value_counts()
            
            with st.expander(f"🔍 {idx}. {responsable} - {int(total_mods)} modificaciones"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.write("**Resumen:**")
                    st.metric("Total Modificaciones", int(total_mods))
                    st.metric("Categorías Diferentes", len(tipos_distribucion))
                
                with col2:
                    st.write("**Distribución por Categoría:**")
                    for tipo, cantidad in tipos_distribucion.items():
                        porcentaje = (cantidad / len(datos_responsable)) * 100
                        st.write(f"• **{tipo}**: {cantidad} casos ({porcentaje:.1f}%)")
                
                # Mini gráfico de barras por categoría
                fig_cat = go.Figure(go.Bar(
                    x=tipos_distribucion.values,
                    y=tipos_distribucion.index,
                    orientation='h',
                    marker_color='rgba(100, 150, 200, 0.7)',
                    text=[f'{val} casos' for val in tipos_distribucion.values],
                    textposition='outside'
                ))
                fig_cat.update_layout(
                    title=f"Categorías de {responsable}",
                    xaxis_title="Cantidad de Casos",
                    yaxis_title="Categoría",
                    height=300
                )
                st.plotly_chart(fig_cat, use_container_width=True)
        
        with st.expander("📋 Análisis Detallado - Responsables"):
            st.markdown(generar_analisis_responsables(df_filtrado))
        
        # ==================== 5. ANÁLISIS POR EMPRESA ====================
        st.header("5️⃣ Análisis por Empresa - Desempeño Comparativo")
        
        modificaciones_por_empresa = df_filtrado.groupby('EMPRESA')['CANTIDAD MODIFICADA'].sum()
        modificaciones_por_empresa_sorted = modificaciones_por_empresa.sort_values(ascending=False)
        
        col9, col10 = st.columns(2)
        
        with col9:
            total_emp = modificaciones_por_empresa_sorted.sum()
            porcentajes_emp = (modificaciones_por_empresa_sorted / total_emp) * 100
            
            fig_empresas = go.Figure(go.Bar(
                x=modificaciones_por_empresa_sorted.values,
                y=modificaciones_por_empresa_sorted.index,
                orientation='h',
                marker_color='rgba(54, 162, 235, 0.7)',
                text=[f'{val:,.0f} ({pct:.1f}%)' for val, pct in zip(modificaciones_por_empresa_sorted.values, porcentajes_emp.values)],
                textposition='outside'
            ))
            
            fig_empresas.update_layout(
                title="Modificaciones por Empresa",
                xaxis_title="Cantidad",
                yaxis_title="Empresa"
            )
            st.plotly_chart(fig_empresas, use_container_width=True)
        
        with col10:
            labels_emp = [
                f"{emp} ({cant:,.0f}) - {pct:.1f}%" 
                for emp, cant, pct in zip(modificaciones_por_empresa_sorted.index, modificaciones_por_empresa_sorted.values, porcentajes_emp.values)
            ]
            
            fig_pie_emp = go.Figure(data=[go.Pie(
                labels=labels_emp, 
                values=modificaciones_por_empresa_sorted.values,
                hole=.3
            )])
            fig_pie_emp.update_layout(title="Distribución por Empresa")
            st.plotly_chart(fig_pie_emp, use_container_width=True)
        
        with st.expander("📋 Análisis Detallado - Empresas"):
            st.markdown(generar_analisis_empresas(df_filtrado))
        
        # ==================== 6. ANÁLISIS POR ÁREA/FUNDO ====================
        st.header("6️⃣ Análisis por Área/Fundo")
        
        modificaciones_por_area = df_filtrado.groupby('ÁREA/FUNDO INVOLUCRADA')['CANTIDAD MODIFICADA'].sum()
        modificaciones_por_area_sorted = modificaciones_por_area.sort_values(ascending=True)
        
        fig_area = go.Figure(go.Bar(
            x=modificaciones_por_area_sorted.values,
            y=modificaciones_por_area_sorted.index,
            orientation='h',
            marker_color='rgba(50, 171, 96, 0.6)',
            text=[f'{val:,.0f}' for val in modificaciones_por_area_sorted.values],
            textposition='outside'
        ))
        fig_area.update_layout(
            title="Total de Modificaciones por Área/Fundo",
            xaxis_title="Cantidad",
            yaxis_title="Área/Fundo"
        )
        st.plotly_chart(fig_area, use_container_width=True)
        
        # ==================== 7. RESUMEN EJECUTIVO ====================
        st.header("📊 Resumen Ejecutivo")
        
        resumen = f"""
        **CONCLUSIONES PRINCIPALES:**
        
        1. **Volumen de Incidencias:** {indicadores['Total Modificaciones']:,.0f} modificaciones en {len(df_filtrado):,} registros
        
        2. **Concentración de Problemas:** 
           - Top 5 responsables concentran {(top_5_responsables.sum() / df_filtrado['CANTIDAD MODIFICADA'].sum() * 100):.1f}% de todas las modificaciones
           - Empresa principal: {modificaciones_por_empresa.idxmax()} con {modificaciones_por_empresa.max():,.0f} modificaciones
           - Tipo principal: {df_filtrado['TIPO INCIDENCIA'].value_counts().idxmax()} ({df_filtrado['TIPO INCIDENCIA'].value_counts().max():,.0f} casos)
        
        3. **Tendencia:** {'📈 CRECIENTE' if (modificaciones_por_semana.iloc[-1] - modificaciones_por_semana.iloc[0]) > 0 else '📉 DECRECIENTE'} 
           (Semana {modificaciones_por_semana.index[0]}: {modificaciones_por_semana.iloc[0]:,.0f} → Semana {modificaciones_por_semana.index[-1]}: {modificaciones_por_semana.iloc[-1]:,.0f})
        
        4. **Recomendaciones Críticas:**
           ✓ Implementar auditoría operativa en las áreas/empresas con mayor cantidad de incidencias
           ✓ Establecer plan de capacitación especializado para los Top 5 responsables
           ✓ Realizar análisis de causa raíz del tipo de incidencia más frecuente
           ✓ Implementar sistema de alertas tempranas para semanas con incrementos > 20%
        """
        
        st.success(resumen)
        
        # ==================== 8. TABLA DE DATOS ====================
        st.header("📋 Datos Filtrados")
        st.dataframe(df_filtrado, use_container_width=True)

if __name__ == "__main__":
    main()