import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from datos_app import cargar_datos, cargar_metricas, cargar_modelo

AZUL, VERDE, GRIS, ROJO, NARANJA = "#5B6CFF", "#2BB673", "#B0B7C3", "#E5534B", "#F2A541"
CATEGORICAS = ["campaign_id", "age", "gender", "interest1", "interest2", "interest3"]
BASE = ["impressions", "clicks", "spent"]


def preparar_features(df, columnas):
    """Arma la matriz X igual que el notebook: CTR, CPC y CPM se derivan de impresiones, clics y gasto."""
    X = df.copy()
    for c in CATEGORICAS:
        if c in X.columns:
            X[c] = X[c].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    for c in BASE:
        X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0).astype(float)
    imp, clk, gas = X["impressions"], X["clicks"], X["spent"]
    X["ctr"] = np.where(imp > 0, clk / imp.where(imp > 0, 1), 0)
    X["cpc"] = np.where(clk > 0, gas / clk.where(clk > 0, 1), 0)
    X["cpm"] = np.where(imp > 0, gas / imp.where(imp > 0, 1) * 1000, 0)
    return X[columnas]


def _nivel(p, umbral):
    if p >= max(umbral, 0.65):
        return "Alta", VERDE
    if p >= umbral:
        return "Media", NARANJA
    return "Baja", ROJO


def _info_modelo(metricas):
    nombre = metricas.get("modelo_seleccionado", "Random Forest")
    fila = next((m for m in metricas.get("clasificacion", []) if m.get("modelo") == nombre), None)
    c = st.columns(5)
    c[0].metric("Modelo", nombre)
    if fila:
        c[1].metric("ROC-AUC (test)", f"{fila['roc_auc']:.3f}")
        c[2].metric("Accuracy", f"{fila['accuracy']:.3f}")
        c[3].metric("Precisión", f"{fila['precision']:.3f}")
        c[4].metric("Recall", f"{fila['recall']:.3f}")

    with st.expander("Métricas y comparación Random Forest vs AdaBoost"):
        comp = pd.DataFrame(metricas.get("clasificacion", []))
        if not comp.empty:
            st.dataframe(comp.rename(columns={"modelo": "Modelo", "accuracy": "Accuracy",
                                              "precision": "Precisión", "recall": "Recall",
                                              "f1": "F1", "roc_auc": "ROC-AUC"}).round(3),
                         hide_index=True, width="stretch")
        imp = metricas.get("importancia_permutacion", {}).get(nombre)
        if imp:
            s = pd.Series(imp).sort_values()
            fig = px.bar(s, orientation="h", color_discrete_sequence=[AZUL],
                         labels={"value": "Caída del AUC al permutar", "index": "Variable"},
                         title=f"Importancia por permutación — {nombre}")
            fig.update_layout(height=360, showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, width="stretch")
        st.caption(f"Métricas sobre el 25 % de anuncios reservados para prueba. "
                   f"ROI invirtiendo en todos: {metricas.get('roi_sin_modelo', float('nan')):.2f} · "
                   f"ROI invirtiendo solo en el top {metricas.get('top_porcentaje_optimo', '—')} % "
                   f"elegido por el modelo: {metricas.get('roi_con_modelo', float('nan')):.2f}.")


def _opciones(datos, col):
    vals = datos[col].astype(str).unique()
    return sorted(vals, key=lambda v: (not v.lstrip("-").isdigit(), int(v) if v.lstrip("-").isdigit() else 0, v))


def _formulario(datos):
    st.markdown("##### 1. Público y campaña")
    c = st.columns(3)
    campana = c[0].selectbox("Campaña", _opciones(datos, "campaign_id"), key="pred_campana")
    edad = c[1].selectbox("Rango de edad", _opciones(datos, "age"), key="pred_edad")
    genero = c[2].selectbox("Género", _opciones(datos, "gender"), key="pred_genero",
                            format_func=lambda g: {"M": "Masculino", "F": "Femenino"}.get(g, g))
    c = st.columns(3)
    intereses = [c[i].selectbox(f"Interés {i + 1}", _opciones(datos, f"interest{i + 1}"),
                                key=f"pred_interes{i + 1}") for i in range(3)]

    segmento = datos[(datos["campaign_id"] == campana) & (datos["age"] == edad) & (datos["gender"] == genero)]
    ref = segmento if len(segmento) >= 3 else datos[datos["campaign_id"] == campana]
    st.markdown("##### 2. Desempeño esperado del anuncio")
    if segmento.empty:
        st.warning("Esta combinación de campaña, edad y género no aparece en los datos: la predicción es "
                   "una extrapolación del modelo.")
    st.caption(f"Valores iniciales = mediana de {len(ref)} anuncios "
               f"{'del mismo segmento' if ref is segmento else 'de la misma campaña'}.")
    c = st.columns(3)
    impresiones = c[0].number_input("Impresiones", min_value=1, max_value=5_000_000, step=1000,
                                    value=int(max(ref["impressions"].median(), 1)), key=f"pred_imp_{campana}_{edad}_{genero}")
    clics = c[1].number_input("Clics", min_value=0, max_value=int(impresiones), step=1,
                              value=int(min(ref["clicks"].median(), impresiones)), key=f"pred_clk_{campana}_{edad}_{genero}")
    gasto = c[2].number_input("Gasto (USD)", min_value=0.0, max_value=50_000.0, step=5.0,
                              value=float(round(ref["spent"].median(), 2)), key=f"pred_gas_{campana}_{edad}_{genero}")
    return pd.DataFrame([{"campaign_id": campana, "age": edad, "gender": genero,
                          "interest1": intereses[0], "interest2": intereses[1], "interest3": intereses[2],
                          "impressions": impresiones, "clicks": clics, "spent": gasto}])


def _indicador(p, umbral):
    nivel, color = _nivel(p, umbral)
    st.markdown(f"**Probabilidad de conversión** · <span style='color:{color}'><b>{nivel}</b></span>",
                unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=round(p * 100, 1), number={"suffix": "%", "font": {"size": 44, "color": color}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
               "steps": [{"range": [0, umbral * 100], "color": "#F4F5F7"},
                         {"range": [umbral * 100, 100], "color": "#E8F7EF"}],
               "threshold": {"line": {"color": "black", "width": 3}, "value": umbral * 100}}))
    fig.update_layout(height=250, margin=dict(l=30, r=30, t=20, b=10))
    st.plotly_chart(fig, width="stretch")


def _curva_gasto(fila, modelo, columnas, umbral):
    """Probabilidad al escalar el gasto manteniendo CPM y CTR del anuncio."""
    f = fila.iloc[0]
    gastos = np.linspace(max(f["spent"] * 0.1, 0.5), max(f["spent"] * 3, 5), 40)
    escala = gastos / f["spent"] if f["spent"] > 0 else gastos
    sim = pd.concat([fila] * len(gastos), ignore_index=True)
    sim["spent"] = gastos
    sim["impressions"] = np.maximum(f["impressions"] * escala, 1)
    sim["clicks"] = f["clicks"] * escala
    proba = modelo.predict_proba(preparar_features(sim, columnas))[:, 1]
    fig = go.Figure(go.Scatter(x=gastos, y=proba * 100, mode="lines", line=dict(color=AZUL, width=3),
                               name="Probabilidad"))
    fig.add_hline(y=umbral * 100, line_dash="dash", line_color=GRIS, annotation_text="Umbral")
    fig.add_vline(x=f["spent"], line_dash="dot", line_color=VERDE, annotation_text="Gasto actual")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), yaxis_range=[0, 100],
                      xaxis_title="Gasto del anuncio (USD)", yaxis_title="Probabilidad (%)")
    st.plotly_chart(fig, width="stretch")
    st.caption("Escala impresiones y clics junto con el gasto (mismo CPM y CTR). Los árboles predicen "
               "en escalones, por eso la curva no es suave.")


def _prediccion_individual(datos, modelo, regresor, columnas, umbral, valor):
    fila = _formulario(datos)
    X = preparar_features(fila, columnas)
    p = float(modelo.predict_proba(X)[0, 1])
    conv = float(max(regresor.predict(preparar_features(fila, list(regresor.feature_names_in_)))[0], 0)) \
        if regresor is not None else np.nan
    gasto = float(fila["spent"].iloc[0])

    st.markdown("##### 3. Resultado")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        _indicador(p, umbral)
    with c2:
        decision = p >= umbral
        (st.success if decision else st.warning)(
            f"**{'Invertir' if decision else 'No priorizar'}:** el modelo estima {p:.1%} de probabilidad de "
            f"lograr al menos una conversión aprobada (umbral {umbral:.0%}).")
        k = st.columns(3)
        k[0].metric("CTR", f"{X['ctr'].iloc[0] * 100:.4f} %")
        k[1].metric("CPC", f"${X['cpc'].iloc[0]:,.2f}")
        k[2].metric("CPM", f"${X['cpm'].iloc[0]:,.2f}")
        if not np.isnan(conv):
            ingreso = conv * valor
            k = st.columns(3)
            k[0].metric("Conversiones esperadas", f"{conv:.2f}", help="Modelo de regresión (modelo_regresion.pkl)")
            k[1].metric("Ingreso esperado", f"${ingreso:,.0f}", help=f"Conversiones × ${valor:,.0f}")
            k[2].metric("ROI esperado", f"{(ingreso - gasto) / gasto:.2f}" if gasto > 0 else "—")
    st.markdown("##### ¿Cómo cambia la probabilidad si invierto más o menos?")
    _curva_gasto(fila, modelo, columnas, umbral)


def _plantilla(datos):
    cols = CATEGORICAS + BASE
    return datos[cols].head(5).to_csv(index=False).encode("utf-8")


def _prediccion_lote(datos, modelo, columnas, umbral, valor):
    origen = st.radio("Anuncios a evaluar", ["Subir un CSV", "Anuncios históricos del dataset"],
                      horizontal=True, key="pred_origen")
    if origen == "Subir un CSV":
        st.caption("Columnas necesarias: " + ", ".join(f"`{c}`" for c in CATEGORICAS + BASE) +
                   ". CTR, CPC y CPM se calculan solos.")
        st.download_button("⬇️ Descargar plantilla", _plantilla(datos), file_name="plantilla_prediccion.csv",
                           mime="text/csv", key="pred_plantilla")
        archivo = st.file_uploader("CSV de anuncios", type="csv", key="pred_archivo")
        if archivo is None:
            return
        try:
            lote = pd.read_csv(archivo, dtype={c: str for c in CATEGORICAS})
        except Exception as error:
            st.error(f"No se pudo leer el CSV: {error}")
            return
        faltan = [c for c in CATEGORICAS + BASE if c not in lote.columns]
        if faltan:
            st.error("Faltan columnas: " + ", ".join(f"`{c}`" for c in faltan))
            return
    else:
        st.warning("Estos anuncios incluyen los que el modelo usó para entrenar, así que las probabilidades "
                   "son optimistas. Úsalo para explorar, no para medir el desempeño (eso está arriba, en las "
                   "métricas de test).")
        lote = datos.copy()

    lote = lote.copy()
    lote["probabilidad"] = modelo.predict_proba(preparar_features(lote, columnas))[:, 1]
    lote["prediccion"] = np.where(lote["probabilidad"] >= umbral, "Convierte", "No convierte")
    lote = lote.sort_values("probabilidad", ascending=False).reset_index(drop=True)

    sel = lote[lote["probabilidad"] >= umbral]
    c = st.columns(4)
    c[0].metric("Anuncios evaluados", f"{len(lote):,}")
    c[1].metric("Sobre el umbral", f"{len(sel):,}", f"{len(sel) / len(lote):.0%} del total", delta_color="off")
    c[2].metric("Probabilidad media", f"{lote['probabilidad'].mean():.1%}")
    c[3].metric("Gasto de los seleccionados", f"${sel['spent'].sum():,.0f}",
                f"{sel['spent'].sum() / max(lote['spent'].sum(), 1e-9):.0%} del gasto", delta_color="off")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(lote, x="probabilidad", nbins=25, color="prediccion",
                           color_discrete_map={"Convierte": VERDE, "No convierte": GRIS},
                           labels={"probabilidad": "Probabilidad de conversión", "prediccion": ""})
        fig.add_vline(x=umbral, line_dash="dash", line_color="black")
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")
    with c2:
        if "approved_conversion" in lote.columns:
            _roi_por_top(lote, valor)
        else:
            por = lote.groupby("campaign_id")["probabilidad"].mean().reset_index()
            fig = px.bar(por, x="campaign_id", y="probabilidad", color_discrete_sequence=[AZUL],
                         labels={"campaign_id": "Campaña", "probabilidad": "Probabilidad media"})
            fig.update_xaxes(type="category")
            fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, width="stretch")

    mostrar = [c for c in ["ad_id"] + CATEGORICAS + BASE + ["approved_conversion", "probabilidad", "prediccion"]
               if c in lote.columns]
    st.dataframe(lote[mostrar], hide_index=True, width="stretch",
                 column_config={"probabilidad": st.column_config.ProgressColumn(
                     "Probabilidad", format="%.2f", min_value=0, max_value=1),
                     "spent": st.column_config.NumberColumn("Gasto", format="$%.2f")})
    st.download_button("⬇️ Descargar predicciones (CSV)", lote[mostrar].to_csv(index=False).encode("utf-8"),
                       file_name="predicciones_conversion.csv", mime="text/csv", key="pred_descarga")


def _roi_por_top(lote, valor):
    filas = []
    for pct in range(10, 101, 10):
        top = lote.head(max(1, int(len(lote) * pct / 100)))
        gasto, conv = top["spent"].sum(), top["approved_conversion"].sum()
        filas.append({"top": pct, "ROI": (conv * valor - gasto) / gasto if gasto > 0 else np.nan,
                      "% conversiones retenidas": conv / max(lote["approved_conversion"].sum(), 1e-9) * 100})
    t = pd.DataFrame(filas)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t["top"], y=t["ROI"], mode="lines+markers", name="ROI", line=dict(color=AZUL)))
    fig.add_trace(go.Scatter(x=t["top"], y=t["% conversiones retenidas"], mode="lines", yaxis="y2",
                             name="% conversiones retenidas", line=dict(color=NARANJA, dash="dash")))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"),
                      xaxis_title="Top % de anuncios según el modelo", yaxis_title="ROI",
                      yaxis2=dict(title="% conversiones", overlaying="y", side="right", range=[0, 105]))
    st.plotly_chart(fig, width="stretch")


def render():
    st.subheader("Predicción de conversión")
    st.caption("Estima la probabilidad de que un anuncio logre al menos una conversión aprobada, con el "
               "modelo de clasificación entrenado en el notebook (`modelo_conversion.pkl`).")

    datos, metricas = cargar_datos(), cargar_metricas()
    modelo = cargar_modelo("modelo_conversion")
    try:
        regresor = cargar_modelo("modelo_regresion")
    except Exception:
        regresor = None
    columnas = list(modelo.feature_names_in_)

    _info_modelo(metricas)

    c1, c2 = st.columns(2)
    umbral = c1.slider("Umbral de decisión", 0.05, 0.95, 0.50, 0.05, key="pred_umbral",
                       help="Probabilidad mínima para recomendar invertir en el anuncio. Subirlo hace al "
                            "modelo más exigente (menos anuncios, mayor precisión).")
    valor = c2.number_input("Valor de una conversión (USD)", min_value=1.0, max_value=10000.0,
                            value=float(metricas.get("valor_conversion_supuesto", 100.0)), step=10.0,
                            key="pred_valor")

    modo = st.segmented_control("Modo", ["Un anuncio", "Varios anuncios (CSV)"], default="Un anuncio",
                                key="pred_modo") or "Un anuncio"
    st.divider()
    if modo == "Un anuncio":
        _prediccion_individual(datos, modelo, regresor, columnas, umbral, valor)
    else:
        _prediccion_lote(datos, modelo, columnas, umbral, valor)

    with st.expander("¿Cómo funciona la predicción?"):
        st.markdown(
            "- **Objetivo:** `convierte = 1` si el anuncio tuvo al menos una conversión aprobada.\n"
            "- **Variables:** campaña, edad, género, 3 intereses, impresiones, clics, gasto, CTR, CPC y CPM. "
            "`total_conversion` se excluye para evitar fuga de información.\n"
            "- **Modelos:** Random Forest y AdaBoost con `GridSearchCV` (5 particiones, ROC-AUC). Se queda el "
            "de mayor AUC en test.\n"
            "- **Conversiones esperadas y ROI:** salen del modelo de regresión que también usa la pestaña de "
            "recomendación.\n\n"
            "**Limitación:** con 761 anuncios el AUC ronda 0,6–0,65; la probabilidad orienta, no garantiza.")
