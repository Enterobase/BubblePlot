import os
import json
import pandas as pd

# ================= CONFIG =================
AMR_TSV = "/home/ang24/PycharmProjects/genSim/BubblePlot/data/AMR.tsv"
HC_TSV  = "/home/ang24/PycharmProjects/genSim/BubblePlot/data/HC.tsv"

SEP = "\t"   # both files are TSV

STRAIN_COL = "Uberstrain"
HC500 = "HC500"
HC100 = "HC100"

AMR_DRUGS = [
    "Isoniazid", "Rifampicin", "Ethambutol", "Pyrazinamide",
    "Levofloxacin", "Moxifloxacin",
    "Bedaquiline", "Linezolid",
    "Clofazimine", "Cycloserine", "Delamanid",
    "Amikacin", "Streptomycin",
    "Ethionamide", "p-Aminosalicylic acid",
    "Capreomycin", "Kanamycin"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_JSON = "hc500_hc100_drug_pie.json"
out_path = os.path.join(BASE_DIR, OUTPUT_JSON)

# ------------------------------------------------
# Load data
# ------------------------------------------------
df_amr = pd.read_csv(AMR_TSV, sep=SEP, low_memory=False)
df_hc  = pd.read_csv(HC_TSV,  sep=SEP, low_memory=False)

df_amr.columns = df_amr.columns.str.strip()
df_hc.columns  = df_hc.columns.str.strip()

# Sanity check (do NOT remove)
missing = set(AMR_DRUGS) - set(df_amr.columns)
if missing:
    raise RuntimeError(f"Missing AMR columns: {missing}")

# ------------------------------------------------
# Merge AMR + HC
# ------------------------------------------------
df = df_amr.merge(
    df_hc[[STRAIN_COL, HC500, HC100]],
    on=STRAIN_COL,
    how="inner"
)

# ------------------------------------------------
# Clean HC columns
# ------------------------------------------------
df[HC500] = pd.to_numeric(df[HC500], errors="coerce")
df[HC100] = pd.to_numeric(df[HC100], errors="coerce")

df = df.dropna(subset=[HC500, HC100])

df[HC500] = df[HC500].astype(int)
df[HC100] = df[HC100].astype(int)

print("Total merged rows:", len(df))
print("Unique HC500:", df[HC500].nunique())
print("Unique HC100:", df[HC100].nunique())

# ------------------------------------------------
# Build hierarchy (DO NOT DROP EMPTY LEVELS)
# ------------------------------------------------
hc500_nodes = []

for hc500, g500 in df.groupby(HC500):
    hc100_nodes = []

    for hc100, g100 in g500.groupby(HC100):
        drug_nodes = []

        for drug in AMR_DRUGS:
            resistant = g100[drug].apply(
                lambda x: pd.notna(x) and x != "-" and str(x).lower() != "false"
            ).sum()

            if resistant > 0:
                drug_nodes.append({
                    "name": drug,
                    "value": int(resistant)
                })

        # ✅ ALWAYS keep HC100 (even if drug_nodes is empty)
        hc100_nodes.append({
            "name": f"HC100_{hc100}",
            "hc100": hc100,
            "value": len(g100),
            "children": drug_nodes   # may be empty
        })

    # ✅ ALWAYS keep HC500
    hc500_nodes.append({
        "name": f"HC500_{hc500}",
        "hc500": hc500,
        "value": len(g500),
        "children": hc100_nodes
    })

# ------------------------------------------------
# Final hierarchy
# ------------------------------------------------
hierarchy = {
    "name": "MTB",
    "children": hc500_nodes
}

with open(out_path, "w") as f:
    json.dump(hierarchy, f, indent=2)

print("Written:", out_path)
print("HC500 nodes:", len(hc500_nodes))
print("Example HC500 children:", len(hc500_nodes[0]["children"]) if hc500_nodes else 0)
