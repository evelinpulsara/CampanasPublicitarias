import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from datos_app import cargar_datos, cargar_metricas

AZUL, VERDE, GRIS, ROJO = "#5B6CFF", "#2BB673", "#B0B7C3", "#E5534B"
COLORES_CAMPANA = {"916": "#F2A541", "936": AZUL, "1178": "#14B8A6"}
DIMENSIONES = {"Campaña": "campaign_id", "Edad": "age", "Género": "gender"}
SUMABLES = ["impressions", "clicks", "spent", "approved_conversion"]
METRICAS = {
    "ROI": ("roi", "{:.2f}"),
    "CPA (USD)": ("cpa", "${:,.2f}"),
    "CTR (%)": ("ctr_pct", "{:.4f} %"),
    "CPC (USD)": ("cpc", "${:,.2f}"),
    "CPM (USD)": ("cpm", "${:,.2f}"),
    "Conversión por clic (%)": ("conv_rate_pct", "{:.1f} %"),
    "% anuncios que convierten": ("pct_convierten", "{:.1f} %"),
}


def _dividir(a, b):
    return a / b if b else np.nan


def _kpis(d, valor):
    """KPIs agregados: se calculan sobre las sumas, no promediando ratios por anuncio."""
    imp, clk, gas, conv = (float(d[c].sum()) for c in SUMABLES)
    ingreso = conv * valor
    return {"anuncios": len(d), "impressions": imp, "clicks": clk, "spent": gas,
            "approved_conversion": conv, "ingreso": ingreso,
            "ctr": _dividir(clk, imp), "cpc": _dividir(gas, clk),
            "cpm": _dividir(gas, imp) * 1000 if imp else np.nan,
            "conv_rate": _dividir(conv, clk), "cpa": _dividir(gas, conv),
            "roi": _dividir(ingreso - gas, gas),
            "pct_convierten": (d["approved_conversion"] >= 1).mean() * 100 if len(d) else np.nan}


def _kpis_por(d, columna, valor):
    filas = [{columna: g, **_kpis(grupo, valor)} for g, grupo in d.groupby(columna)]
    t = pd.DataFrame(filas)
    t["ctr_pct"] = t["ctr"] * 100
    t["conv_rate_pct"] = t["conv_rate"] * 100
    t["% gasto"] = t["spent"] / t["spent"].sum() * 100
    t["% conversiones"] = t["approved_conversion"] / max(t["approved_conversion"].sum(), 1) * 100
    if columna == "age":
        t = t.sort_values(columna)
    elif columna == "campaign_id":
        t = t.sort_values(columna, key=lambda s: s.astype(int))
    return t.reset_index(drop=True)


def _filtros(datos, metricas):
    c1, c2, c3, c4 = st.columns([1, 1, 0.8, 1])
    campanas_todas = sorted(datos["campaign_id"].unique(), key=int)
    edades_todas = sorted(datos["age"].unique())
    generos_todos = sorted(datos["gender"].unique())
    campanas = c1.multiselect("Campaña", campanas_todas, default=campanas_todas, key="kpi_campanas")
    edades = c2.multiselect("Rango de edad", edades_todas, default=edades_todas, key="kpi_edades")
    generos = c3.multiselect("Género", generos_todos, default=generos_todos, key="kpi_generos",
                             format_func=lambda g: {"M": "Masculino", "F": "Femenino"}.get(g, g))
    valor = c4.number_input("Valor de una conversión (USD)", min_value=1.0, max_value=10000.0,
                            value=float(metricas.get("valor_conversion_supuesto", 100.0)), step=10.0,
                            key="kpi_valor",
                            help="El dataset no trae ingresos: el ROI usa este supuesto "
                                 "(el mismo del notebook, 100 USD por defecto).")
    return campanas, edades, generos, valor


def _delta(actual, total, invertir=False, pct=False):
    if pd.isna(actual) or pd.isna(total) or total == 0:
        return None
    cambio = (actual - total) / abs(total) * 100
    return f"{cambio:+.1f} % vs total"


def _tarjetas(k, k_total, filtrado):
    fila1 = st.columns(5)
    fila1[0].metric("Anuncios", f"{k['anuncios']:,}",
                    f"{k['anuncios'] / k_total['anuncios'] * 100:.0f} % del total" if filtrado else None,
                    delta_color="off")
    fila1[1].metric("Impresiones", f"{k['impressions']:,.0f}")
    fila1[2].metric("Clics", f"{k['clicks']:,.0f}")
    fila1[3].metric("Gasto", f"${k['spent']:,.0f}")
    fila1[4].metric("Conversiones aprobadas", f"{k['approved_conversion']:,.0f}")

    d = (lambda a, b: _delta(a, b)) if filtrado else (lambda a, b: None)
    fila2 = st.columns(5)
    fila2[0].metric("CTR", f"{k['ctr'] * 100:.4f} %", d(k["ctr"], k_total["ctr"]),
                    help="Clics / impresiones")
    fila2[1].metric("CPC", f"${k['cpc']:,.2f}", d(k["cpc"], k_total["cpc"]), delta_color="inverse",
                    help="Gasto / clics")
    fila2[2].metric("CPM", f"${k['cpm']:,.2f}", d(k["cpm"], k_total["cpm"]), delta_color="inverse",
                    help="Gasto / impresiones × 1000")
    fila2[3].metric("CPA", "—" if pd.isna(k["cpa"]) else f"${k['cpa']:,.2f}",
                    d(k["cpa"], k_total["cpa"]), delta_color="inverse",
                    help="Gasto / conversiones aprobadas")
    fila2[4].metric("ROI", "—" if pd.isna(k["roi"]) else f"{k['roi']:.2f}",
                    d(k["roi"], k_total["roi"]),
                    help="(conversiones × valor − gasto) / gasto")


def _grafico_por_dimension(t, columna, nombre_dim, metrica):
    col_metrica, _ = METRICAS[metrica]
    c1, c2 = st.columns(2)
    with c1:
        largo = t.melt(id_vars=columna, value_vars=["% gasto", "% conversiones"],
                       var_name="Indicador", value_name="Porcentaje")
        fig = px.bar(largo, x=columna, y="Porcentaje", color="Indicador", barmode="group",
                     text_auto=".1f", color_discrete_map={"% gasto": GRIS, "% conversiones": AZUL},
                     labels={columna: nombre_dim}, title="Participación en gasto vs conversiones")
        fig.update_xaxes(type="category")
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")
    with c2:
        tm = t.dropna(subset=[col_metrica])
        fig = px.bar(tm, x=columna, y=col_metrica, text_auto=".3s" if col_metrica != "roi" else ".2f",
                     color_discrete_sequence=[VERDE if col_metrica in ("roi", "ctr_pct", "conv_rate_pct",
                                                                       "pct_convierten") else ROJO],
                     labels={columna: nombre_dim, col_metrica: metrica}, title=f"{metrica} por {nombre_dim.lower()}")
        if col_metrica == "roi":
            fig.add_hline(y=0, line_color="black", line_width=1)
        fig.update_xaxes(type="category")
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width="stretch")


def _tabla(t, columna, nombre_dim):
    mostrar = t[[columna, "anuncios", "impressions", "clicks", "spent", "approved_conversion",
                 "ctr_pct", "cpc", "cpm", "cpa", "roi", "pct_convierten"]].rename(columns={
        columna: nombre_dim, "anuncios": "Anuncios", "impressions": "Impresiones", "clicks": "Clics",
        "spent": "Gasto", "approved_conversion": "Conversiones", "ctr_pct": "CTR %", "cpc": "CPC",
        "cpm": "CPM", "cpa": "CPA", "roi": "ROI", "pct_convierten": "% anuncios que convierten"})
    st.dataframe(mostrar, hide_index=True, width="stretch",
                 column_config={"Impresiones": st.column_config.NumberColumn(format="localized"),
                                "Clics": st.column_config.NumberColumn(format="localized"),
                                "Gasto": st.column_config.NumberColumn(format="dollar"),
                                "Conversiones": st.column_config.NumberColumn(format="%.0f"),
                                "CTR %": st.column_config.NumberColumn(format="%.4f"),
                                "CPC": st.column_config.NumberColumn(format="$%.2f"),
                                "CPM": st.column_config.NumberColumn(format="$%.2f"),
                                "CPA": st.column_config.NumberColumn(format="$%.2f"),
                                "ROI": st.column_config.NumberColumn(format="%.2f"),
                                "% anuncios que convierten": st.column_config.ProgressColumn(
                                    format="%.1f%%", min_value=0, max_value=100)})


def _mapa_calor(d, valor, metrica):
    col_metrica, _ = METRICAS[metrica]
    filas = []
    for (edad, genero), g in d.groupby(["age", "gender"]):
        k = _kpis(g, valor)
        k["ctr_pct"], k["conv_rate_pct"] = k["ctr"] * 100, k["conv_rate"] * 100
        filas.append({"Edad": edad, "Género": genero, "valor": k[col_metrica], "anuncios": k["anuncios"]})
    if not filas:
        return
    m = pd.DataFrame(filas).pivot(index="Edad", columns="Género", values="valor").sort_index()
    escala = "RdYlGn_r" if col_metrica in ("cpa", "cpc", "cpm") else "RdYlGn"
    fig = px.imshow(m, text_auto=".2f" if col_metrica not in ("ctr_pct",) else ".4f", aspect="auto",
                    color_continuous_scale=escala, labels={"color": metrica})
    fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")


def _dispersion(d):
    fig = px.scatter(d, x="spent", y="approved_conversion", color="campaign_id",
                     color_discrete_map=COLORES_CAMPANA, opacity=0.65,
                     hover_data={"age": True, "gender": True, "interest1": True, "clicks": True},
                     labels={"spent": "Gasto del anuncio (USD)", "approved_conversion": "Conversiones aprobadas",
                             "campaign_id": "Campaña", "age": "Edad", "gender": "Género",
                             "interest1": "Interés", "clicks": "Clics"})
    fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")


def render():
    st.subheader("KPIs generales")
    st.caption("Indicadores agregados de los anuncios válidos (tras la limpieza del notebook). "
               "Los ratios se calculan sobre los totales filtrados, no como promedio de cada anuncio.")

    datos, metricas = cargar_datos(), cargar_metricas()
    campanas, edades, generos, valor = _filtros(datos, metricas)
    if not (campanas and edades and generos):
        st.warning("Selecciona al menos una campaña, un rango de edad y un género.")
        return

    d = datos[datos["campaign_id"].isin(campanas) & datos["age"].isin(edades)
              & datos["gender"].isin(generos)]
    if d.empty:
        st.warning("No hay anuncios con esa combinación de filtros. Ojo: tras la limpieza, la campaña "
                   "1178 solo tiene anuncios de hombres (las filas corruptas eliminadas eran de mujeres).")
        return

    filtrado = len(d) < len(datos)
    k, k_total = _kpis(d, valor), _kpis(datos, valor)
    _tarjetas(k, k_total, filtrado)
    if filtrado:
        st.caption("Las flechas comparan la selección con el total de anuncios. En CPC, CPM y CPA, "
                   "verde significa más barato.")

    st.markdown("#### Desglose")
    c1, c2 = st.columns(2)
    nombre_dim = c1.radio("Ver por", list(DIMENSIONES), horizontal=True, key="kpi_dimension")
    metrica = c2.selectbox("Métrica a comparar", list(METRICAS), key="kpi_metrica")
    columna = DIMENSIONES[nombre_dim]
    t = _kpis_por(d, columna, valor)
    _grafico_por_dimension(t, columna, nombre_dim, metrica)
    _tabla(t, columna, nombre_dim)

    mejor = t.dropna(subset=["roi"]).sort_values("roi", ascending=False)
    if len(mejor) > 1:
        a, b = mejor.iloc[0], mejor.iloc[-1]
        st.info(f"**{nombre_dim} con mejor ROI:** {a[columna]} (ROI {a['roi']:.2f}, CPA ${a['cpa']:,.2f}). "
                f"**Peor:** {b[columna]} (ROI {b['roi']:.2f}, CPA ${b['cpa']:,.2f}).")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### {metrica}: edad × género")
        _mapa_calor(d, valor, metrica)
    with c2:
        st.markdown("#### Gasto vs conversiones por anuncio")
        _dispersion(d)

    with st.expander("Ver datos filtrados"):
        cols = ["ad_id", "campaign_id", "age", "gender", "interest1", "interest2", "interest3",
                "impressions", "clicks", "spent", "approved_conversion"]
        st.dataframe(d[[c for c in cols if c in d.columns]], hide_index=True, width="stretch")
        st.download_button("⬇️ Descargar selección (CSV)", d.to_csv(index=False).encode("utf-8"),
                           file_name="anuncios_filtrados.csv", mime="text/csv", key="kpi_descarga")

    with st.expander("¿Cómo se calculan los KPIs?"):
        st.markdown(
            "| KPI | Fórmula |\n|---|---|\n"
            "| CTR | clics / impresiones |\n| CPC | gasto / clics |\n| CPM | gasto / impresiones × 1000 |\n"
            "| Conversión por clic | conversiones aprobadas / clics |\n| CPA | gasto / conversiones aprobadas |\n"
            "| ROI | (conversiones × valor de conversión − gasto) / gasto |\n\n"
            "Mismas fórmulas que la sección 2 del notebook.")
