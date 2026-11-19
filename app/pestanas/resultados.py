import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from datos_app import cargar_ab, cargar_atribucion

AZUL, VERDE, GRIS, ROJO = "#5B6CFF", "#2BB673", "#B0B7C3", "#E5534B"
COLORES_CAMPANA = {"916": "#F2A541", "936": AZUL, "1178": "#9B5DE5"}
MODELOS_ATRIB = {"Último contacto": "last_touch", "Lineal": "lineal", "Shapley": "shapley"}


def _formato_p(p):
    if pd.isna(p):
        return "—"
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def _valor_metrica(metrica, v):
    if pd.isna(v):
        return "—"
    if metrica == "Tasa de conversión":
        return f"{v * 100:.1f} %"
    if metrica == "CTR":
        return f"{v * 100:.4f} %"
    return f"${v:,.2f}"


def _ab_global(ab):
    glob = ab[ab["tipo"] == "global"].copy()
    st.markdown("#### Pruebas globales")
    st.caption("¿Hay alguna diferencia entre los grupos del factor? (p ajustado con Bonferroni)")
    glob["Resultado"] = np.where(glob["significativo"], "✅ Hay diferencias", "➖ Sin evidencia")
    glob["p ajustado"] = glob["p_bonferroni"].apply(_formato_p)
    glob["Efecto"] = glob["tamano_efecto"].map("{:.2f}".format) + " (" + glob["tipo_efecto"] + ")"
    st.dataframe(glob[["metrica", "factor", "prueba", "p ajustado", "Efecto", "Resultado"]]
                 .rename(columns={"metrica": "Métrica", "factor": "Factor", "prueba": "Prueba"}),
                 hide_index=True, width="stretch")


def _ab_pares(ab):
    pares = ab[ab["tipo"] == "pareada"].copy()
    st.markdown("#### Comparaciones entre pares de grupos")
    c1, c2 = st.columns(2)
    metrica = c1.selectbox("Métrica", list(pares["metrica"].unique()))
    factor = c2.selectbox("Factor", list(pares["factor"].unique()))
    sel = pares[(pares["metrica"] == metrica) & (pares["factor"] == factor)].copy()

    grupos = pd.concat([sel[["grupo_a", "valor_a", "n_a"]].set_axis(["grupo", "valor", "n"], axis=1),
                        sel[["grupo_b", "valor_b", "n_b"]].set_axis(["grupo", "valor", "n"], axis=1)])
    grupos = grupos.drop_duplicates("grupo").sort_values("grupo")
    etiqueta = "mediana" if metrica in ("CTR", "CPA") else "proporción"
    escala = 100 if metrica in ("Tasa de conversión", "CTR") else 1
    grupos["mostrar"] = grupos["valor"] * escala

    col_g, col_t = st.columns([1, 1.6])
    with col_g:
        fig = px.bar(grupos, x="grupo", y="mostrar", text_auto=".3g", color_discrete_sequence=[AZUL],
                     labels={"grupo": factor, "mostrar": f"{metrica} ({etiqueta}{', %' if escala == 100 else ''})"},
                     hover_data={"n": True})
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, width="stretch")
    with col_t:
        sel["Comparación"] = sel["grupo_a"] + " vs " + sel["grupo_b"]
        sel["A"] = sel["valor_a"].apply(lambda v: _valor_metrica(metrica, v))
        sel["B"] = sel["valor_b"].apply(lambda v: _valor_metrica(metrica, v))
        sel["p ajustado"] = sel["p_bonferroni"].apply(_formato_p)
        sel["Resultado"] = np.where(sel["significativo"], "✅ " + sel["conclusion"], "➖ " + sel["conclusion"])
        st.dataframe(sel[["Comparación", "A", "B", "prueba", "p ajustado", "potencia", "Resultado"]]
                     .rename(columns={"prueba": "Prueba", "potencia": "Potencia"}),
                     hide_index=True, width="stretch",
                     column_config={"Potencia": st.column_config.ProgressColumn(
                         format="%.2f", min_value=0, max_value=1)})
    st.caption("Potencia < 0,80 en una comparación no significativa significa que faltan datos para "
               "afirmar que los grupos son iguales.")


def _ab_potencia(ab):
    pares = ab[ab["tipo"] == "pareada"].copy()
    pares["Comparación"] = (pares["metrica"] + " · " + pares["factor"] + ": "
                            + pares["grupo_a"] + " vs " + pares["grupo_b"])
    pares["Resultado"] = np.where(pares["significativo"], "Significativa", "No significativa")
    fig = px.scatter(pares, x="tamano_efecto", y="potencia", color="Resultado", symbol="metrica",
                     hover_name="Comparación",
                     color_discrete_map={"Significativa": VERDE, "No significativa": GRIS},
                     labels={"tamano_efecto": "Tamaño del efecto", "potencia": "Potencia", "metrica": "Métrica"})
    fig.add_hline(y=0.8, line_dash="dash", line_color=ROJO, annotation_text="Potencia 0,80")
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")


def _render_ab():
    ab = cargar_ab()
    pares = ab[ab["tipo"] == "pareada"]
    c = st.columns(3)
    c[0].metric("Pruebas realizadas", len(ab))
    c[1].metric("Pares significativos", f"{int(pares['significativo'].sum())} de {len(pares)}")
    c[2].metric("Corrección", "Bonferroni")
    _ab_global(ab)
    _ab_pares(ab)
    st.markdown("#### Potencia vs tamaño del efecto")
    _ab_potencia(ab)


def _render_atribucion():
    at = cargar_atribucion()
    modelo_nombre = st.radio("Modelo de atribución", list(MODELOS_ATRIB), horizontal=True, index=2)
    m = MODELOS_ATRIB[modelo_nombre]
    col_conv, col_cpa, col_roi = f"atribucion_{m}", f"cpa_{m}", f"roi_{m}"

    por_campana = at.groupby("campana").agg(spent=("spent", "sum"), clicks=("clicks", "sum"),
                                            impressions=("impressions", "sum"),
                                            conversiones=(col_conv, "sum")).reset_index()
    por_campana["CPA"] = por_campana["spent"] / por_campana["conversiones"].replace(0, np.nan)
    por_campana["CTR %"] = por_campana["clicks"] / por_campana["impressions"] * 100
    por_campana["% conversiones"] = por_campana["conversiones"] / por_campana["conversiones"].sum() * 100
    por_campana["% gasto"] = por_campana["spent"] / por_campana["spent"].sum() * 100

    st.markdown("#### Comparación de canales por campaña")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        largo = por_campana.melt(id_vars="campana", value_vars=["% gasto", "% conversiones"],
                                 var_name="Indicador", value_name="Porcentaje")
        fig = px.bar(largo, x="campana", y="Porcentaje", color="Indicador", barmode="group", text_auto=".1f",
                     color_discrete_map={"% gasto": GRIS, "% conversiones": AZUL},
                     labels={"campana": "Campaña"})
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, width="stretch")
        st.caption("Si una campaña se lleva más % del gasto que % de las conversiones, es menos eficiente.")
    with c2:
        st.dataframe(por_campana[["campana", "spent", "conversiones", "CPA", "CTR %"]]
                     .rename(columns={"campana": "Campaña", "spent": "Gasto", "conversiones": "Conversiones"}),
                     hide_index=True, width="stretch",
                     column_config={"Gasto": st.column_config.NumberColumn(format="$%.0f"),
                                    "CPA": st.column_config.NumberColumn(format="$%.2f"),
                                    "Conversiones": st.column_config.NumberColumn(format="%.1f"),
                                    "CTR %": st.column_config.NumberColumn(format="%.4f")})

    st.markdown("#### Canales (campaña × interés)")
    validos = at[(at["spent"] > 0) & (at[col_conv] > 0)].copy()
    c1, c2 = st.columns(2)
    campanas = c1.multiselect("Campañas", sorted(at["campana"].unique()), default=sorted(at["campana"].unique()))
    minimo = c2.slider("Conversiones mínimas del canal", 0, int(at[col_conv].max()), 3,
                       help="Los canales con muy pocas conversiones tienen ROI extremos poco confiables.")
    validos = validos[validos["campana"].isin(campanas) & (validos[col_conv] >= minimo)]
    if validos.empty:
        st.warning("No hay canales con esos filtros.")
        return

    fig = px.scatter(validos, x=col_cpa, y=col_roi, size="spent", color="campana", hover_name="canal",
                     color_discrete_map=COLORES_CAMPANA, log_x=True, size_max=40,
                     hover_data={col_conv: ":.1f", "spent": ":$,.0f", "ctr": ":.5f"},
                     labels={col_cpa: "CPA (USD, escala log)", col_roi: "ROI", "campana": "Campaña",
                             col_conv: "Conversiones atribuidas", "spent": "Gasto"})
    fig.add_hline(y=0, line_color="black", line_width=1)
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption("Arriba a la izquierda están los mejores canales: barato por conversión y alto ROI. "
               "El tamaño de la burbuja es el gasto.")

    c1, c2 = st.columns(2)
    for col, titulo, orden in [(c1, "🏆 Canales más rentables", False), (c2, "⚠️ Canales menos rentables", True)]:
        top = validos.sort_values(col_roi, ascending=orden).head(8)
        col.markdown(f"**{titulo}**")
        col.dataframe(top[["canal", "spent", col_conv, col_cpa, col_roi]]
                      .rename(columns={"canal": "Canal", "spent": "Gasto", col_conv: "Conversiones",
                                       col_cpa: "CPA", col_roi: "ROI"}),
                      hide_index=True, width="stretch",
                      column_config={"Gasto": st.column_config.NumberColumn(format="$%.0f"),
                                     "CPA": st.column_config.NumberColumn(format="$%.2f"),
                                     "ROI": st.column_config.NumberColumn(format="%.2f"),
                                     "Conversiones": st.column_config.NumberColumn(format="%.1f")})

    st.markdown("#### Conversiones atribuidas según cada modelo")
    top10 = at.sort_values("approved_conversion", ascending=False).head(10)
    largo = top10.melt(id_vars="canal", value_vars=[f"atribucion_{v}" for v in MODELOS_ATRIB.values()],
                       var_name="Modelo", value_name="Conversiones")
    largo["Modelo"] = largo["Modelo"].map({f"atribucion_{v}": k for k, v in MODELOS_ATRIB.items()})
    fig = px.bar(largo, x="canal", y="Conversiones", color="Modelo", barmode="group",
                 color_discrete_sequence=[AZUL, GRIS, VERDE], labels={"canal": "Canal"})
    fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, width="stretch")

    with st.expander("Ver tabla completa de atribución"):
        st.dataframe(at.drop(columns=["campana", "interes"]), hide_index=True, width="stretch")
        st.download_button("⬇️ Descargar CSV", at.to_csv(index=False).encode("utf-8"),
                           file_name="atribucion_resultados.csv", mime="text/csv")


def render():
    st.subheader("Resultados de A/B testing y atribución")
    sub1, sub2 = st.tabs(["🧪 A/B testing", "🔀 Atribución y comparación de canales"])
    with sub1:
        _render_ab()
    with sub2:
        _render_atribucion()
