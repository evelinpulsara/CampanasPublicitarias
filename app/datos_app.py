import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from recomendador import RecomendadorInversion

DIR_DATOS = Path(__file__).parent / "datos"

ARCHIVOS = {
    "datos": "datos_limpios.csv",
    "modelo_conversion": "modelo_conversion.pkl",
    "modelo_regresion": "modelo_regresion.pkl",
    "metricas": "metricas_modelos.json",
    "ab": "ab_resultados.csv",
    "atribucion": "atribucion_resultados.csv",
}

TIPOS_TEXTO = {"campaign_id": str, "interest1": str, "interest2": str, "interest3": str,
               "age": str, "gender": str}


def archivos_faltantes():
    return [nombre for nombre in ARCHIVOS.values() if not (DIR_DATOS / nombre).exists()]


@st.cache_data
def cargar_datos():
    return pd.read_csv(DIR_DATOS / ARCHIVOS["datos"], dtype=TIPOS_TEXTO)


@st.cache_data
def cargar_metricas():
    with open(DIR_DATOS / ARCHIVOS["metricas"], encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def cargar_ab():
    return pd.read_csv(DIR_DATOS / ARCHIVOS["ab"], dtype={"grupo_a": str, "grupo_b": str})


@st.cache_data
def cargar_atribucion():
    df = pd.read_csv(DIR_DATOS / ARCHIVOS["atribucion"])
    partes = df["canal"].str.split(" - ", n=1, expand=True)
    df["campana"] = partes[0].str.strip()
    df["interes"] = partes[1].str.replace("Int_", "", regex=False).str.strip()
    return df


@st.cache_resource
def cargar_modelo(clave):
    return joblib.load(DIR_DATOS / ARCHIVOS[clave])


@st.cache_resource(show_spinner="Construyendo curvas de respuesta por segmento...")
def obtener_recomendador(valor_conversion, campanas):
    datos = cargar_datos()
    datos = datos[datos["campaign_id"].isin(campanas)]
    return RecomendadorInversion(cargar_modelo("modelo_regresion"), datos, valor_conversion)
