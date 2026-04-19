"""
FundMatch Pro — Versión Flask para PythonAnywhere
Ejecuta: python flask_app.py (local) o configura como WSGI en PythonAnywhere
"""

import warnings
warnings.filterwarnings("ignore")

from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
import os

app = Flask(__name__)

# ─── RUTAS A LOS EXCEL ────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONDOS_PATH   = os.path.join(BASE_DIR, "Base_de_datos_fondos.xlsx")
PERFILES_PATH = os.path.join(BASE_DIR, "dataset_final_con_perfiles__1_.xlsx")

# ─── CONSTANTES ───────────────────────────────────────────────────────────
NOMBRES_CLUSTER = {
    0: "Monetario / Liquidez",
    1: "Renta Fija Conservadora",
    2: "Mixto Conservador",
    3: "Mixto Equilibrado",
    4: "Renta Variable Moderada",
    5: "Renta Variable Dinamica",
    6: "Alta Conviccion / Alternativo",
}

RIESGO_SRRI = {
    "Bajo":       (1, 3),
    "Medio-Bajo": (2, 4),
    "Medio":      (3, 5),
    "Medio-Alto": (4, 6),
    "Alto":       (5, 7),
}

HORIZONTE_RETORNO = {
    "<1 anyo":   "Total Ret 1 Yr (Daily) EUR",
    "1-3 anyos": "Total Ret Annlzd 3 Yr (Daily) EUR",
    "3-5 anyos": "Total Ret Annlzd 5 Yr (Daily) EUR",
    "5-10 anyos":"Total Ret Annlzd 5 Yr (Daily) EUR",
    ">10 anyos": "Total Ret Annlzd 10 Yr (Daily) EUR",
}

# ─── CARGA Y CLUSTERING ───────────────────────────────────────────────────
def cargar_y_clusterizar():
    fondos   = pd.read_excel(FONDOS_PATH)
    perfiles = pd.read_excel(PERFILES_PATH)

    # Inferir SRRI
    cat_srri_map = {
        "Money Market":1,"Bond":2,"Cautious":3,"Moderate":4,
        "Flexible":4,"Aggressive":5,"Equity":5,"Technology":6,"Alternative":6,
    }
    mask_srri = fondos["Surveyed KIID SRRI"].isna()
    for kw, val in cat_srri_map.items():
        fondos.loc[mask_srri & fondos["Morningstar Category"].str.contains(kw, na=False, case=False), "Surveyed KIID SRRI"] = val

    features = [
        "Surveyed KIID SRRI","Total Ret Annlzd 3 Yr (Daily) EUR",
        "Total Ret Annlzd 5 Yr (Daily) EUR","Std Dev 3 Yr (Mo-End) EUR",
        "Std Dev 5 Yr (Mo-End) EUR","Max Drawdown Gross Return 10Yr (Qtr End)",
        "KIID Ongoing Charge","Morningstar Rating Overall",
    ]
    X = fondos[features].copy()
    imputer  = SimpleImputer(strategy="median")
    X_imp    = imputer.fit_transform(X)
    X_scaled = StandardScaler().fit_transform(X_imp)

    kmeans = KMeans(n_clusters=7, random_state=42, n_init=20)
    labels = kmeans.fit_predict(X_scaled)

    srri_medio = pd.DataFrame({"c": labels, "s": X_imp[:, 0]}).groupby("c")["s"].mean().sort_values()
    remap = {old: new for new, old in enumerate(srri_medio.index)}
    fondos["Cluster"] = [remap[c] for c in labels]
    fondos["Familia"] = fondos["Cluster"].map(NOMBRES_CLUSTER)

    ret3 = fondos["Total Ret Annlzd 3 Yr (Daily) EUR"].fillna(0)
    std3 = fondos["Std Dev 3 Yr (Mo-End) EUR"].replace(0, np.nan).fillna(10)
    fondos["Score"] = (
        (ret3 / std3) * 0.45
        + fondos["Morningstar Rating Overall"].fillna(3) * 0.30
        - fondos["KIID Ongoing Charge"].fillna(1) * 0.15
        + np.log1p(fondos["Fund Size EUR"].fillna(1e6)) * 0.10
    )
    return fondos, perfiles


print("Cargando datos y calculando clustering...")
FONDOS, PERFILES = cargar_y_clusterizar()
print(f"Listo: {len(FONDOS)} fondos en {FONDOS['Familia'].nunique()} familias.")


# ─── TEMPLATE HTML ────────────────────────────────────────────────────────
HTML_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FundMatch Pro</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f4f8; color: #1a1a1a; }
  header { background: #1a3a5c; color: white; padding: 16px 32px; display:flex; align-items:center; gap:12px; }
  header h1 { font-size: 1.5rem; }
  nav { background: #2e7d9c; display: flex; gap: 0; }
  nav a { color: white; text-decoration: none; padding: 12px 20px; font-size: .9rem; }
  nav a:hover, nav a.active { background: #1a3a5c; }
  main { max-width: 1100px; margin: 24px auto; padding: 0 16px; }
  .card { background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
  .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 20px; }
  .metric { background: white; border-radius: 10px; padding: 16px 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.07); }
  .metric .val { font-size: 2rem; font-weight: 800; color: #1a3a5c; }
  .metric .lbl { font-size: .82rem; color: #666; margin-top: 4px; }
  h2 { color: #1a3a5c; font-size: 1.2rem; margin-bottom: 14px; }
  h3 { color: #2e7d9c; font-size: 1rem; margin: 14px 0 8px; }
  label { font-size: .88rem; font-weight: 600; display: block; margin-bottom: 4px; margin-top: 12px; }
  select, input[type=number], input[type=text] {
    width: 100%; padding: 9px 12px; border: 1px solid #ccc; border-radius: 7px; font-size: .9rem; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
  button.primary {
    background: #1a3a5c; color: white; border: none; padding: 12px 28px;
    border-radius: 8px; font-size: 1rem; cursor: pointer; margin-top: 20px; width: 100%; }
  button.primary:hover { background: #2e7d9c; }
  table { width: 100%; border-collapse: collapse; font-size: .82rem; }
  th { background: #1a3a5c; color: white; padding: 9px 10px; text-align: left; }
  td { padding: 8px 10px; border-bottom: 1px solid #eee; }
  tr:nth-child(even) td { background: #f8fafc; }
  .badge { display:inline-block; background:#2e7d9c; color:white; border-radius:20px; padding:2px 9px; font-size:.78rem; }
  .srri-bar { display:inline-flex; gap:2px; }
  .srri-dot { width:10px; height:10px; border-radius:50%; }
  .tag { background:#e8f4f8; color:#1a3a5c; border-radius:5px; padding:2px 7px; font-size:.78rem; margin:2px; display:inline-block; }
  .alert { background: #fff3cd; border-left: 4px solid #f0a500; padding: 12px 16px; border-radius:6px; margin-bottom:16px; }
  @media(max-width:700px){ .grid-4{grid-template-columns:1fr 1fr;} .form-grid{grid-template-columns:1fr;} }
</style>
</head>
<body>
<header>
  <span style="font-size:1.8rem">📈</span>
  <div>
    <h1>FundMatch Pro</h1>
    <div style="font-size:.8rem;opacity:.8">Motor inteligente de fondos de inversión</div>
  </div>
</header>
<nav>
  <a href="/" {% if page=='home' %}class="active"{% endif %}>🏠 Dashboard</a>
  <a href="/recomendar" {% if page=='recomendar' %}class="active"{% endif %}>🤖 Recomendador</a>
  <a href="/buscador" {% if page=='buscador' %}class="active"{% endif %}>🔍 Buscador</a>
  <a href="/familias" {% if page=='familias' %}class="active"{% endif %}>📊 Familias</a>
</nav>
<main>
{{ content }}
</main>
</body>
</html>
"""

def render(page, content):
    return render_template_string(HTML_BASE, page=page, content=content)


# ─── RUTAS ────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    stats = FONDOS.groupby("Familia").agg(
        N=("Name","count"),
        SRRI=("Surveyed KIID SRRI","mean"),
        Ret3A=("Total Ret Annlzd 3 Yr (Daily) EUR","median"),
        Vol3A=("Std Dev 3 Yr (Mo-End) EUR","median"),
    ).round(2)

    rows = ""
    for fam, row in stats.iterrows():
        rows += f"<tr><td>{fam}</td><td>{int(row['N'])}</td><td>{row['SRRI']:.1f}</td><td>{row['Ret3A']:.1f}%</td><td>{row['Vol3A']:.1f}%</td></tr>"

    perfiles_dist = PERFILES["Perfil_Nombre"].value_counts()
    perfil_rows = "".join(
        f"<tr><td>{p}</td><td>{n}</td></tr>"
        for p, n in perfiles_dist.items()
    )

    content = f"""
    <div class="grid-4">
      <div class="metric"><div class="val">{len(FONDOS):,}</div><div class="lbl">Fondos analizados</div></div>
      <div class="metric"><div class="val">7</div><div class="lbl">Familias de clustering</div></div>
      <div class="metric"><div class="val">{len(PERFILES)}</div><div class="lbl">Perfiles de inversores</div></div>
      <div class="metric"><div class="val">{FONDOS['Morningstar Category'].nunique()}</div><div class="lbl">Categorías Morningstar</div></div>
    </div>
    <div class="card">
      <h2>Distribución de fondos por familia de clustering</h2>
      <table>
        <thead><tr><th>Familia</th><th>Fondos</th><th>SRRI Medio</th><th>Rent. 3A Mediana</th><th>Vol. 3A Mediana</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="card">
      <h2>Distribución de perfiles MiFID en la base de clientes</h2>
      <table>
        <thead><tr><th>Perfil</th><th>Clientes</th></tr></thead>
        <tbody>{perfil_rows}</tbody>
      </table>
    </div>
    """
    return render("home", content)


@app.route("/recomendar", methods=["GET", "POST"])
def recomendar():
    resultado_html = ""

    if request.method == "POST":
        riesgo       = request.form.get("riesgo", "Medio")
        horizonte    = request.form.get("horizonte", "3-5 anyos")
        capital      = float(request.form.get("capital", 50000))
        esg          = request.form.get("esg", "Indiferente")
        restriccion  = request.form.get("restriccion", "Sin restricciones")
        top_n        = int(request.form.get("top_n", 10))

        srri_min, srri_max = RIESGO_SRRI.get(riesgo, (1, 7))
        ret_col = HORIZONTE_RETORNO.get(horizonte, "Total Ret Annlzd 3 Yr (Daily) EUR")
        std_col = "Std Dev 3 Yr (Mo-End) EUR" if "3" in ret_col else "Std Dev 5 Yr (Mo-End) EUR"

        mask = (
            FONDOS["Surveyed KIID SRRI"].between(srri_min, srri_max)
            & (FONDOS["Minimum Investment (Base Currency)"].fillna(0) <= capital)
        )

        if esg in ("Muy importante", "Importante"):
            mask &= FONDOS["Morningstar Category"].str.contains("ESG|Sustain|SRI|Green", na=False, case=False)
        if restriccion == "No RV":
            mask &= ~FONDOS["Morningstar Category"].str.contains("Equity", na=False, case=False)
        elif restriccion == "No RF":
            mask &= ~FONDOS["Morningstar Category"].str.contains("Bond|Fixed", na=False, case=False)
        elif restriccion == "Solo ESG":
            mask &= FONDOS["Morningstar Category"].str.contains("ESG|Sustain|SRI", na=False, case=False)

        sub = FONDOS[mask].copy()
        if sub.empty:
            resultado_html = '<div class="alert">No se encontraron fondos compatibles. Prueba a relajar alguna restricción.</div>'
        else:
            ret_val = sub[ret_col].fillna(sub["Total Ret Annlzd 3 Yr (Daily) EUR"].fillna(0))
            std_val = sub[std_col].replace(0, np.nan).fillna(10)
            sub["Score_Final"] = (
                (ret_val / std_val) * 0.50
                + sub["Morningstar Rating Overall"].fillna(3) * 0.30
                - sub["KIID Ongoing Charge"].fillna(1) * 0.10
                + np.log1p(sub["Fund Size EUR"].fillna(1e6)) * 0.10
            )
            top = sub.nlargest(top_n, "Score_Final")[
                ["Name","Familia","Surveyed KIID SRRI","Morningstar Rating Overall",ret_col,"KIID Ongoing Charge","Score_Final"]
            ].reset_index(drop=True)

            rows = ""
            for _, r in top.iterrows():
                ret_v = f"{r[ret_col]:.1f}%" if pd.notna(r[ret_col]) else "N/D"
                rows += f"""<tr>
                  <td>{r['Name'][:45]}</td>
                  <td><span class="tag">{r['Familia']}</span></td>
                  <td>{int(r['Surveyed KIID SRRI']) if pd.notna(r['Surveyed KIID SRRI']) else '-'}</td>
                  <td>{'★' * int(r['Morningstar Rating Overall']) if pd.notna(r['Morningstar Rating Overall']) else '-'}</td>
                  <td>{ret_v}</td>
                  <td>{r['KIID Ongoing Charge']:.2f}% if pd.notna(r['KIID Ongoing Charge']) else 'N/D'</td>
                  <td><b>{r['Score_Final']:.2f}</b></td>
                </tr>"""
            resultado_html = f"""
            <div class="card">
              <h2>✅ Top {top_n} fondos recomendados</h2>
              <table>
                <thead><tr><th>Fondo</th><th>Familia</th><th>SRRI</th><th>Rating</th><th>Rent.</th><th>TER</th><th>Score</th></tr></thead>
                <tbody>{rows}</tbody>
              </table>
            </div>"""

    riesgo_opts = "".join(f"<option>{v}</option>" for v in ["Bajo","Medio-Bajo","Medio","Medio-Alto","Alto"])
    horizonte_opts = "".join(f"<option>{v}</option>" for v in ["<1 anyo","1-3 anyos","3-5 anyos","5-10 anyos",">10 anyos"])
    esg_opts = "".join(f"<option>{v}</option>" for v in ["Indiferente","No importante","Importante","Muy importante"])
    rest_opts = "".join(f"<option>{v}</option>" for v in ["Sin restricciones","No RV","No RF","No derivados","No materias primas","Solo ESG"])

    content = f"""
    <div class="card">
      <h2>🤖 Introduce el perfil del inversor</h2>
      <form method="POST">
        <div class="form-grid">
          <div>
            <label>Tolerancia al riesgo</label>
            <select name="riesgo">{riesgo_opts}</select>
            <label>Horizonte de inversión</label>
            <select name="horizonte">{horizonte_opts}</select>
            <label>Capital disponible (€)</label>
            <input type="number" name="capital" value="50000" min="0" step="1000">
          </div>
          <div>
            <label>Preferencia ESG</label>
            <select name="esg">{esg_opts}</select>
            <label>Restricciones de inversión</label>
            <select name="restriccion">{rest_opts}</select>
            <label>Número de resultados (Top-N)</label>
            <input type="number" name="top_n" value="10" min="5" max="25">
          </div>
        </div>
        <button class="primary" type="submit">🔍 Buscar fondos recomendados</button>
      </form>
    </div>
    {resultado_html}
    """
    return render("recomendar", content)


@app.route("/buscador", methods=["GET","POST"])
def buscador():
    query    = request.form.get("query", "")
    srri_max = int(request.form.get("srri_max", 7))
    rating_min = int(request.form.get("rating_min", 1))

    mask = (
        (FONDOS["Surveyed KIID SRRI"].fillna(7) <= srri_max)
        & (FONDOS["Morningstar Rating Overall"].fillna(0) >= rating_min)
    )
    if query:
        mask &= FONDOS["Name"].str.contains(query, case=False, na=False) | \
                FONDOS["ISIN"].str.contains(query, case=False, na=False)

    sub = FONDOS[mask].nlargest(50, "Score")[
        ["Name","ISIN","Familia","Surveyed KIID SRRI","Morningstar Rating Overall",
         "Total Ret Annlzd 3 Yr (Daily) EUR","KIID Ongoing Charge","Score"]
    ].reset_index(drop=True)

    rows = ""
    for _, r in sub.iterrows():
        ret3 = f"{r['Total Ret Annlzd 3 Yr (Daily) EUR']:.1f}%" if pd.notna(r["Total Ret Annlzd 3 Yr (Daily) EUR"]) else "N/D"
        rows += f"<tr><td>{r['Name'][:45]}</td><td>{r['ISIN']}</td><td><span class='tag'>{r['Familia']}</span></td><td>{int(r['Surveyed KIID SRRI']) if pd.notna(r['Surveyed KIID SRRI']) else '-'}</td><td>{ret3}</td><td>{r['Score']:.2f}</td></tr>"

    content = f"""
    <div class="card">
      <h2>🔍 Buscador de Fondos</h2>
      <form method="POST" style="display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end">
        <div style="flex:1;min-width:180px">
          <label>Nombre / ISIN</label>
          <input type="text" name="query" value="{query}" placeholder="Buscar...">
        </div>
        <div style="min-width:120px">
          <label>SRRI máximo</label>
          <select name="srri_max">{"".join(f'<option {"selected" if str(i)==str(srri_max) else ""}>{i}</option>' for i in range(1,8))}</select>
        </div>
        <div style="min-width:140px">
          <label>Rating mínimo ★</label>
          <select name="rating_min">{"".join(f'<option {"selected" if str(i)==str(rating_min) else ""}>{i}</option>' for i in range(1,6))}</select>
        </div>
        <button class="primary" type="submit" style="width:auto;padding:9px 20px;margin:0">Buscar</button>
      </form>
    </div>
    <div class="card">
      <h2>Resultados ({len(sub)} de {FONDOS[mask].shape[0]:,} fondos)</h2>
      <table>
        <thead><tr><th>Fondo</th><th>ISIN</th><th>Familia</th><th>SRRI</th><th>Rent. 3A</th><th>Score</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return render("buscador", content)


@app.route("/familias")
def familias():
    stats = FONDOS.groupby("Familia").agg(
        N=("Name","count"),
        SRRI=("Surveyed KIID SRRI","mean"),
        Ret3A=("Total Ret Annlzd 3 Yr (Daily) EUR","median"),
        Ret5A=("Total Ret Annlzd 5 Yr (Daily) EUR","median"),
        Vol3A=("Std Dev 3 Yr (Mo-End) EUR","median"),
        TER=("KIID Ongoing Charge","median"),
        Rating=("Morningstar Rating Overall","mean"),
    ).round(2).reset_index()

    cards = ""
    colores = ["#1a3a5c","#2e7d9c","#48a999","#f0a500","#e07b39","#c0392b","#7d3c98"]
    for i, (_, row) in enumerate(stats.iterrows()):
        c = colores[i % len(colores)]
        cards += f"""
        <div style="background:white;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.08);border-top:4px solid {c}">
          <h3 style="color:{c};margin-bottom:12px">{row['Familia']}</h3>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.85rem">
            <div><b>Fondos:</b> {int(row['N'])}</div>
            <div><b>SRRI Medio:</b> {row['SRRI']:.1f}</div>
            <div><b>Rent. 3A:</b> {row['Ret3A']:.1f}%</div>
            <div><b>Rent. 5A:</b> {row['Ret5A']:.1f}% if pd.notna(row['Ret5A']) else 'N/D'</div>
            <div><b>Vol. 3A:</b> {row['Vol3A']:.1f}%</div>
            <div><b>TER:</b> {row['TER']:.2f}%</div>
            <div><b>Rating:</b> {'★' * round(row['Rating'])} ({row['Rating']:.1f})</div>
          </div>
        </div>"""

    content = f"""
    <div class="card">
      <h2>📊 Las 7 Familias de Fondos — Resultado del Clustering K-Means</h2>
      <p style="color:#555;margin-bottom:20px">
        Los 7.004 fondos se agrupan en 7 familias mediante K-Means (k=7) aplicado sobre 8 variables financieras estandarizadas.
        Los clusters se ordenan por SRRI medio ascendente para garantizar interpretabilidad.
      </p>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px">
      {cards}
    </div>
    """
    return render("familias", content)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
