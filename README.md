# Optimización de Campañas Publicitarias

**Integrantes:** Evelin Dayanna Pulsara Madroñero · Deivid Julián Alvarado Morán ·
Giovanny Andrés Zambrano · Esteban Giovanny Meneses Paz

**Dataset:** Facebook Ads Campaign Dataset — https://www.kaggle.com/datasets/madislemsalu/facebook-ad-campaign

## Contenido

| Archivo / carpeta | Qué es |
|---|---|
| `Optimizacion_Campanas_Publicitarias.ipynb` | Notebook completo (secciones 1 a 14): limpieza, KPIs, Random Forest y AdaBoost, ROI, recomendación de inversión, A/B testing, atribución y conclusiones |
| `app/` | App web en Streamlit (dashboard de campañas) lista para desplegar, con los datos y modelos reales |

## Requerimientos del proyecto y dónde se cumplen

| Requerimiento | Notebook | App |
|---|---|---|
| Modelos de predicción de conversión | Secciones 4 a 8 | Pestaña 2 |
| Random Forest y AdaBoost | Secciones 5 a 7 | Pestaña 2 |
| Análisis de ROI y métricas del modelo | Secciones 2, 6 y 9 | Pestañas 1 y 2 |
| A/B testing | Sección 11 | Pestaña 4 |
| Modelos de atribución | Sección 12 | Pestaña 4 |
| App web con dashboard de campañas | — | Pestañas 1 a 4 |
| Recomendación de inversión | Sección 10 | Pestaña 3 |
| Comparación de canales | Sección 12 | Pestañas 1 y 4 |

## Ejecutar el notebook

Abrirlo en Google Colab y usar **Entorno de ejecución → Ejecutar todo**. El dataset se descarga solo de
Kaggle en la sección 1. Tarda unos 5 minutos.

## Desplegar la app en Streamlit Community Cloud

1. Crear un repositorio público en GitHub y subir **el contenido de la carpeta `app/`** (que `app.py`
   quede en la raíz del repositorio).
2. Entrar a https://share.streamlit.io con la cuenta de GitHub → **Create app**.
3. Elegir el repositorio, rama `main` y archivo principal `app.py`.
4. En **Advanced settings**, elegir Python 3.12.
5. **Deploy**. Copiar el link y pegarlo en el informe (sección 7).

`requirements.txt` fija `scikit-learn==1.6.1`, la versión con la que se entrenaron los modelos `.pkl`.
