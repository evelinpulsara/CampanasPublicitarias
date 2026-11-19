import streamlit as st

st.set_page_config(page_title="Optimización de Campañas Publicitarias", page_icon="📈", layout="wide")

from datos_app import DIR_DATOS, archivos_faltantes
from estilo import aplicar_estilo, encabezado, pie
from pestanas import kpis, prediccion, recomendacion, resultados

aplicar_estilo()
encabezado()

faltantes = archivos_faltantes()
if faltantes:
    st.error("Faltan archivos en la carpeta `datos/`: " + ", ".join(f"`{f}`" for f in faltantes))
    st.info(f"Copia en `{DIR_DATOS.name}/` los archivos que exporta el notebook (`parte1_salidas.zip`) "
            "y los CSV de A/B testing y atribución.")
    st.stop()

try:
    from datos_app import cargar_modelo
    cargar_modelo("modelo_conversion")
    cargar_modelo("modelo_regresion")
except Exception as error:
    st.error("No se pudieron cargar los modelos `.pkl`. Casi siempre es porque la versión de "
             "scikit-learn de la app no es la misma de Colab. Revisa `requirements.txt`.")
    st.exception(error)
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📊 KPIs generales", "🎯 Predicción de conversión",
                                  "💰 Recomendación de inversión", "🧪 A/B testing y atribución"])

with tab1:
    kpis.render()
with tab2:
    prediccion.render()
with tab3:
    recomendacion.render()
with tab4:
    resultados.render()

pie()
