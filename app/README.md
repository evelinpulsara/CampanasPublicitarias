# Optimización de Campañas Publicitarias — App web

Dashboard en Streamlit del proyecto de optimización de campañas (Facebook Ads Campaign Dataset).

| Pestaña | Contenido | Responsable |
|---|---|---|
| 1. KPIs generales | KPIs y filtros por campaña, edad y género | Esteban |
| 2. Predicción de conversión | Probabilidad de conversión con `modelo_conversion.pkl` | Esteban |
| 3. Recomendación de inversión | Reparto óptimo del presupuesto con `recomendador.py` | Evelin |
| 4. A/B testing y atribución | Resultados de A/B testing (Deivid) y atribución (Giovanny Andrés) | Evelin |

## Estructura

```
app.py                  # punto de entrada
datos_app.py            # carga de datos y modelos (con caché)
recomendador.py         # motor de recomendación (sección 10 del notebook)
pestanas/
  kpis.py               # pestaña 1
  prediccion.py         # pestaña 2
  recomendacion.py      # pestaña 3
  resultados.py         # pestaña 4
datos/
  datos_limpios.csv         ← sección 13 del notebook
  modelo_conversion.pkl     ← sección 13 del notebook
  modelo_regresion.pkl      ← sección 13 del notebook
  metricas_modelos.json     ← sección 13 del notebook
  ab_resultados.csv         ← sección 11 del notebook
  atribucion_resultados.csv ← sección 12 del notebook
requirements.txt
```

## Pestañas 1 y 2 (Esteban)

**Pestaña 1 — KPIs generales** (`pestanas/kpis.py`)
- Filtros por campaña, rango de edad y género, más el valor supuesto de una conversión (para el ROI).
- 10 tarjetas: anuncios, impresiones, clics, gasto, conversiones, CTR, CPC, CPM, CPA y ROI, con
  comparación contra el total cuando hay filtros.
- Desglose por campaña, edad o género: % del gasto vs % de las conversiones, métrica elegida, tabla de KPIs
  y el mejor/peor grupo por ROI.
- Mapa de calor edad × género y dispersión gasto vs conversiones.
- Descarga de los anuncios filtrados.

**Pestaña 2 — Predicción de conversión** (`pestanas/prediccion.py`)
- Métricas del modelo elegido (ROC-AUC, accuracy, precisión, recall), comparación RF vs AdaBoost e
  importancia por permutación (desde `metricas_modelos.json`).
- **Un anuncio:** formulario (campaña, edad, género, intereses, impresiones, clics, gasto) → probabilidad
  con `modelo_conversion.pkl`, decisión según el umbral, conversiones, ingreso y ROI esperados
  (`modelo_regresion.pkl`) y curva de probabilidad según el gasto.
- **Varios anuncios:** CSV propio (con plantilla descargable) o los anuncios históricos → ranking,
  histograma, ROI según el top % elegido por el modelo y descarga de predicciones.
- CTR, CPC y CPM se calculan igual que en el notebook (`preparar_features`).

> Nota de datos: tras la limpieza (761 anuncios), la campaña 1178 solo tiene anuncios de hombres.
> Las dos pestañas lo avisan cuando se elige esa combinación.

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Importante: versión de scikit-learn

Los `.pkl` solo se cargan con la **misma versión de scikit-learn** con la que se entrenaron.
En Colab ejecuta:

```python
import sklearn, sys; print(sklearn.__version__, sys.version)
```

y pon esa versión en `requirements.txt` (línea `scikit-learn==...`).
