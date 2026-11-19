import numpy as np
import pandas as pd
import joblib


class RecomendadorInversion:
    """Reparte un presupuesto entre segmentos (campaña x edad x género)
    maximizando las conversiones esperadas según el modelo de regresión."""

    def __init__(self, modelo, datos, valor_conversion,
                 segmento=("campaign_id", "age", "gender"),
                 puntos=40, factor_max=1.5, min_anuncios=3):
        self.modelo = modelo
        self.datos = datos.copy()
        self.valor = float(valor_conversion)
        self.segmento = list(segmento)
        self.puntos = puntos
        self.factor_max = factor_max
        self.min_anuncios = min_anuncios
        self.columnas = list(modelo.feature_names_in_)
        for c in self.segmento:
            self.datos[c] = self.datos[c].astype(str)
        self.curvas = self._construir_curvas()

    @classmethod
    def desde_archivos(cls, ruta_modelo, ruta_datos, valor_conversion, **kwargs):
        datos = pd.read_csv(ruta_datos, dtype={"campaign_id": str, "interest1": str,
                                               "interest2": str, "interest3": str})
        return cls(joblib.load(ruta_modelo), datos, valor_conversion, **kwargs)

    @staticmethod
    def _envolvente_concava(xs, ys):
        hull = []
        for p in zip(xs, ys):
            while len(hull) >= 2:
                (ox, oy), (ax, ay) = hull[-2], hull[-1]
                if (ax - ox) * (p[1] - oy) - (ay - oy) * (p[0] - ox) >= 0:
                    hull.pop()
                else:
                    break
            hull.append(p)
        hx, hy = zip(*hull)
        return np.array(hx), np.array(hy)

    def _anuncios_simulados(self, grupo, gastos):
        imp, clk, gas = grupo["impressions"].sum(), grupo["clicks"].sum(), grupo["spent"].sum()
        cpm = gas / imp * 1000 if imp > 0 else 0
        ctr = clk / imp if imp > 0 else 0
        impresiones = np.where(cpm > 0, gastos / max(cpm, 1e-9) * 1000, 0)
        clics = impresiones * ctr
        numericas = {"impressions", "clicks", "spent", "ctr", "cpm", "cpc"}
        base = {c: str(grupo[c].mode().iloc[0]) for c in self.columnas if c not in numericas}
        filas = pd.DataFrame({**base,
                              "impressions": impresiones, "clicks": clics, "spent": gastos,
                              "ctr": ctr, "cpm": cpm,
                              "cpc": np.where(clics > 0, gastos / np.where(clics > 0, clics, 1), 0)})
        return filas[self.columnas]

    def _construir_curvas(self):
        curvas = {}
        for clave, grupo in self.datos.groupby(self.segmento):
            if len(grupo) < self.min_anuncios or grupo["spent"].max() <= 0:
                continue
            gastos = np.linspace(0, grupo["spent"].max() * self.factor_max, self.puntos)
            conv = np.clip(self.modelo.predict(self._anuncios_simulados(grupo, gastos)), 0, None)
            conv[0] = 0
            conv = np.maximum.accumulate(conv)
            hx, hy = self._envolvente_concava(gastos, conv)
            curvas[clave] = {"n_anuncios": len(grupo), "gastos": gastos, "conv": conv,
                             "hx": hx, "hy": hy,
                             "gasto_historico": grupo["spent"].sum(),
                             "conv_historicas": grupo["approved_conversion"].sum()}
        return curvas

    def conversiones_esperadas(self, clave, inversion):
        c = self.curvas[clave]
        n = c["n_anuncios"]
        return n * np.interp(inversion / n, c["hx"], c["hy"])

    def capacidad_maxima(self):
        return sum(c["n_anuncios"] * c["hx"][-1] for c in self.curvas.values())

    def recomendar(self, presupuesto, solo_rentable=True):
        tramos = []
        for clave, c in self.curvas.items():
            dx, dy = np.diff(c["hx"]), np.diff(c["hy"])
            for a, b in zip(dx, dy):
                if a > 0:
                    tramos.append((b / a, clave, a * c["n_anuncios"]))
        tramos.sort(key=lambda t: t[0], reverse=True)

        asignado, restante = {}, float(presupuesto)
        for pendiente, clave, capacidad in tramos:
            if restante <= 0 or (solo_rentable and pendiente * self.valor <= 1):
                break
            monto = min(capacidad, restante)
            asignado[clave] = asignado.get(clave, 0.0) + monto
            restante -= monto
        return self.evaluar(asignado, presupuesto)

    def reparto_historico(self, presupuesto):
        total = sum(c["gasto_historico"] for c in self.curvas.values())
        return self.evaluar({k: presupuesto * c["gasto_historico"] / total
                             for k, c in self.curvas.items()}, presupuesto)

    def reparto_igual(self, presupuesto):
        return self.evaluar({k: presupuesto / len(self.curvas) for k in self.curvas}, presupuesto)

    def evaluar(self, asignacion, presupuesto):
        filas = []
        for clave, inv in asignacion.items():
            if inv <= 0:
                continue
            conv = self.conversiones_esperadas(clave, inv)
            filas.append({**dict(zip(self.segmento, clave)),
                          "inversion": inv, "conversiones_esperadas": conv,
                          "ingreso_esperado": conv * self.valor})
        tabla = pd.DataFrame(filas)
        if tabla.empty:
            tabla = pd.DataFrame(columns=self.segmento + ["inversion", "conversiones_esperadas",
                                                          "ingreso_esperado"])
        tabla["roi_esperado"] = (tabla["ingreso_esperado"] - tabla["inversion"]) / tabla["inversion"]
        tabla["%_presupuesto"] = tabla["inversion"] / presupuesto * 100
        tabla = tabla.sort_values("inversion", ascending=False).reset_index(drop=True)
        invertido = tabla["inversion"].sum()
        ingreso = tabla["ingreso_esperado"].sum()
        resumen = {"presupuesto": float(presupuesto),
                   "invertido": float(invertido),
                   "sin_invertir": float(presupuesto - invertido),
                   "conversiones_esperadas": float(tabla["conversiones_esperadas"].sum()),
                   "ingreso_esperado": float(ingreso),
                   "roi_esperado": float((ingreso - invertido) / invertido) if invertido > 0 else 0.0}
        return tabla.round(3), resumen
