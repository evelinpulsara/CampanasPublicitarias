import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from datos_app import cargar_datos, cargar_metricas, obtener_recomendador

AZUL, VERDE, GRIS = "#5B6CFF", "#2BB673", "#B0B7C3"


def _etiqueta(fila, segmento):
    return " | ".join(str(fila[c]) for c in segmento)


def _controles(datos, metricas):
    gasto_total = float(datos["spent"].sum())
    defecto = float(metricas.get("presupuesto_ejemplo", round(gasto_total * 0.25, -2)))
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    presupuesto = c1.number_input("Presupuesto a repartir (USD)", min_value=100.0,
                                  max_value=gasto_total * 10, value=defecto, step=100.0)
    valor = c2.number_input("Valor de una conversión (USD)", min_value=1.0, max_value=10000.0,
                            value=float(metricas.get("valor_conversion_supuesto", 100.0)), step=10.0)
    campanas_todas = sorted(datos["campaign_id"].unique())
    campanas = c3.multiselect("Campañas disponibles", campanas_todas, default=campanas_todas)
    solo_rentable = st.toggle("Invertir solo mientras el siguiente dólar sea rentable", value=True,
                              help="Si está activo, el recomendador deja dinero sin invertir cuando "
                                   "una conversión extra ya no paga lo que cuesta.")
    return presupuesto, valor, tuple(sorted(campanas)), solo_rentable


def _tarjetas(resumen, r_hist):
    c = st.columns(4)
    c[0].metric("Invertido", f"${resumen['invertido']:,.0f}",
                f"${resumen['sin_invertir']:,.0f} sin invertir", delta_color="off")
    c[1].metric("Conversiones esperadas", f"{resumen['conversiones_esperadas']:,.1f}",
                f"{resumen['conversiones_esperadas'] - r_hist['conversiones_esperadas']:+,.1f} vs histórico")
    c[2].metric("Ingreso esperado", f"${resumen['ingreso_esperado']:,.0f}")
    c[3].metric("ROI esperado", f"{resumen['roi_esperado']:.2f}",
                f"{resumen['roi_esperado'] - r_hist['roi_esperado']:+.2f} vs histórico")


def _grafico_reparto(tabla, segmento):
    t = tabla.copy()
    t["segmento"] = t.apply(lambda f: _etiqueta(f, segmento), axis=1)
    fig = px.bar(t.sort_values("inversion"), x="inversion", y="segmento", orientation="h",
                 color="roi_esperado", color_continuous_scale=["#C9CEFF", "#2E3BD6"],
                 hover_data={"conversiones_esperadas": ":.1f", "%_presupuesto": ":.1f"},
                 labels={"inversion": "Inversión (USD)", "segmento": "Campaña | Edad | Género",
                         "roi_esperado": "ROI"})
    fig.update_layout(height=max(320, 28 * len(t)), margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")


def _comparar_estrategias(reco, presupuesto, resumen):
    estrategias = pd.DataFrame({
        "Igual por segmento": reco.reparto_igual(presupuesto)[1],
        "Proporcional al histórico": reco.reparto_historico(presupuesto)[1],
        "Modelo (invertir todo)": reco.recomendar(presupuesto, solo_rentable=False)[1],
        "Modelo (solo rentable)": resumen,
    }).T.reset_index(names="estrategia")
    colores = {"Igual por segmento": GRIS, "Proporcional al histórico": GRIS,
               "Modelo (invertir todo)": AZUL, "Modelo (solo rentable)": VERDE}
    c1, c2 = st.columns(2)
    for col, metrica, titulo in [(c1, "conversiones_esperadas", "Conversiones esperadas"),
                                 (c2, "roi_esperado", "ROI esperado")]:
        fig = px.bar(estrategias, x=metrica, y="estrategia", orientation="h", color="estrategia",
                     color_discrete_map=colores, title=titulo, text_auto=".2f")
        fig.update_layout(showlegend=False, height=300, yaxis_title=None, xaxis_title=None,
                          margin=dict(l=0, r=0, t=40, b=0))
        col.plotly_chart(fig, width="stretch")
    return estrategias


def _curva_segmento(reco, tabla, segmento):
    claves = sorted(reco.curvas, key=lambda k: reco.curvas[k]["conv_historicas"], reverse=True)
    elegido = st.selectbox("Segmento", claves, format_func=lambda k: " | ".join(k))
    c = reco.curvas[elegido]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c["gastos"], y=c["conv"], mode="lines", line_shape="hv",
                             name="Predicción del modelo", line=dict(color=GRIS)))
    fig.add_trace(go.Scatter(x=c["hx"], y=c["hy"], mode="lines+markers", name="Envolvente cóncava",
                             line=dict(color=AZUL)))
    fila = tabla[(tabla[segmento].astype(str).apply(tuple, axis=1)) == tuple(elegido)]
    if not fila.empty:
        x = float(fila["inversion"].iloc[0]) / c["n_anuncios"]
        fig.add_trace(go.Scatter(x=[x], y=[np.interp(x, c["hx"], c["hy"])], mode="markers",
                                 marker=dict(size=14, color=VERDE, symbol="star"),
                                 name="Inversión recomendada por anuncio"))
    fig.update_layout(xaxis_title="Gasto por anuncio (USD)", yaxis_title="Conversiones esperadas",
                      height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"{c['n_anuncios']} anuncios en el segmento · gasto histórico ${c['gasto_historico']:,.0f} · "
               f"{c['conv_historicas']:.0f} conversiones históricas")


@st.cache_data(show_spinner=False)
def _sensibilidad(valor, campanas, presupuesto):
    reco = obtener_recomendador(valor, campanas)
    tope = min(presupuesto * 4, reco.capacidad_maxima())
    filas = []
    for p in np.linspace(max(presupuesto * 0.1, 100), tope, 15):
        filas.append({"presupuesto": p,
                      "Modelo": reco.recomendar(p, solo_rentable=False)[1]["roi_esperado"],
                      "Histórico": reco.reparto_historico(p)[1]["roi_esperado"],
                      "rentable": reco.recomendar(p)[1]["invertido"]})
    return pd.DataFrame(filas)


def render():
    st.subheader("Recomendación de inversión por segmento")
    st.caption("El modelo de regresión estima cuántas conversiones da cada segmento (campaña × edad × género) "
               "según el gasto. El presupuesto se reparte dólar a dólar hacia donde más rinde.")

    datos, metricas = cargar_datos(), cargar_metricas()
    presupuesto, valor, campanas, solo_rentable = _controles(datos, metricas)
    if not campanas:
        st.warning("Selecciona al menos una campaña.")
        return

    reco = obtener_recomendador(valor, campanas)
    if not reco.curvas:
        st.warning("Las campañas seleccionadas no tienen segmentos con suficientes anuncios.")
        return

    tabla, resumen = reco.recomendar(presupuesto, solo_rentable=solo_rentable)
    _, r_hist = reco.reparto_historico(presupuesto)
    segmento = reco.segmento

    _tarjetas(resumen, r_hist)
    if resumen["sin_invertir"] > 1:
        st.info(f"Con un valor de ${valor:,.0f} por conversión, invertir más de "
                f"${resumen['invertido']:,.0f} ya no es rentable: el resto conviene guardarlo o "
                f"probar nuevos públicos.")
    if tabla.empty:
        st.warning("Con este valor por conversión ningún segmento es rentable.")
        return

    st.markdown("#### ¿Dónde invertir?")
    c1, c2 = st.columns([1.4, 1])
    with c1:
        _grafico_reparto(tabla, segmento)
    with c2:
        mostrar = tabla.rename(columns={"campaign_id": "Campaña", "age": "Edad", "gender": "Género",
                                        "inversion": "Inversión", "conversiones_esperadas": "Conversiones",
                                        "ingreso_esperado": "Ingreso", "roi_esperado": "ROI",
                                        "%_presupuesto": "% presupuesto"})
        st.dataframe(mostrar, hide_index=True, width="stretch",
                     column_config={"Inversión": st.column_config.NumberColumn(format="$%.0f"),
                                    "Ingreso": st.column_config.NumberColumn(format="$%.0f"),
                                    "Conversiones": st.column_config.NumberColumn(format="%.1f"),
                                    "ROI": st.column_config.NumberColumn(format="%.2f"),
                                    "% presupuesto": st.column_config.ProgressColumn(
                                        format="%.1f%%", min_value=0, max_value=100)})
        st.download_button("⬇️ Descargar recomendación (CSV)", tabla.to_csv(index=False).encode("utf-8"),
                           file_name="recomendacion_inversion.csv", mime="text/csv")

    st.markdown("#### Modelo vs repartos ingenuos")
    _comparar_estrategias(reco, presupuesto, resumen)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Curva de respuesta de un segmento")
        _curva_segmento(reco, tabla, segmento)
    with c2:
        st.markdown("#### ROI según el tamaño del presupuesto")
        sens = _sensibilidad(valor, campanas, presupuesto)
        fig = px.line(sens, x="presupuesto", y=["Modelo", "Histórico"], markers=True,
                      color_discrete_sequence=[AZUL, GRIS],
                      labels={"value": "ROI esperado", "presupuesto": "Presupuesto (USD)", "variable": ""})
        fig.add_hline(y=0, line_color="black", line_width=1)
        fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Presupuesto máximo rentable: ~${sens['rentable'].max():,.0f}. A partir de ahí, "
                   "cada dólar extra trae conversiones que cuestan más de lo que valen.")

    with st.expander("¿Cómo funciona el recomendador?"):
        st.markdown(
            "1. Para cada segmento se arma un **anuncio típico** con su CPM y CTR históricos.\n"
            "2. El **modelo de regresión** predice cuántas conversiones daría ese anuncio con distintos niveles "
            "de gasto: la **curva de respuesta**.\n"
            "3. Como los árboles predicen en escalones, se usa la **envolvente cóncava** de la curva "
            "(rendimientos decrecientes).\n"
            "4. El presupuesto se asigna de forma **voraz**: cada dólar va al segmento con mayor conversión "
            "marginal. Con curvas cóncavas este reparto es óptimo (mochila fraccionaria).\n\n"
            "**Limitaciones:** extrapola hasta 1,5× el gasto máximo observado por anuncio y asume que el CPM y "
            "el CTR de cada segmento se mantienen.")
