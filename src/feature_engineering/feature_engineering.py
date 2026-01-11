import json
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from utils.config_loader import PROJECT_ROOT

def feature_engineering_seattle(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """
    Feature engineering pour prédire TotalGHGEmissions (target).
    - Construit features "physiques" (taille, âge, mix énergétique, ratios, interactions)
    - Ajoute features spatiales simples (Downtown + geo)
    - Supprime colonnes inutiles/ID + fuite (GHGEmissionsIntensity)
    """

    df_fe = df.copy()
    fe_cfg = cfg.feature_engineering
    params = fe_cfg.params
    selection = fe_cfg.selection

    year_ref = params.year_ref
    eps = params.eps

    # =========================
    # 0) Colonnes
    # =========================
    COL_TARGET = "TotalGHGEmissions"
    COL_GFA    = "PropertyGFATotal"
    COL_YEAR   = "YearBuilt"
    COL_FLOOR  = "NumberofFloors"
    COL_BLDGS  = "NumberofBuildings"
    COL_PARK   = "PropertyGFAParking"
    COL_GFA_B  = "PropertyGFABuilding(s)"

    COL_EUI    = "SiteEUI(kBtu/sf)"
    COL_EUI_WN = "SiteEUIWN(kBtu/sf)"
    COL_SITEN  = "SiteEnergyUse(kBtu)"
    COL_SITENW = "SiteEnergyUseWN(kBtu)"

    COL_ELEC_KBTU = "Electricity(kBtu)"
    COL_ELEC_KWH  = "Electricity(kWh)"
    COL_GAS_KBTU  = "NaturalGas(kBtu)"
    COL_GAS_TH    = "NaturalGas(therms)"
    COL_STEAM     = "SteamUse(kBtu)"

    COL_ES     = "ENERGYSTARScore"
    COL_TYPE   = "PrimaryPropertyType"
    COL_BTYPE  = "BuildingType"
    COL_NEI    = "Neighborhood"
    COL_ZIP    = "ZipCode"
    COL_CD     = "CouncilDistrictCode"

    COL_LAT    = "Latitude"
    COL_LON    = "Longitude"

    DROP_ALWAYS = list(fe_cfg.drop_always)
    DROP_LEAKY = list(fe_cfg.drop_leaky)
    DROP_UNIT_DUPLICATES = list(fe_cfg.drop_unit_duplicates)

    # =========================
    # 1) Nettoyage types numériques (coerce)
    # =========================
    numeric_cols = [
        COL_TARGET, COL_GFA, COL_YEAR, COL_FLOOR, COL_BLDGS, COL_PARK, COL_GFA_B,
        COL_EUI, COL_EUI_WN, COL_SITEN, COL_SITENW,
        COL_ELEC_KBTU, COL_GAS_KBTU, COL_STEAM, COL_ES,
        COL_LAT, COL_LON,
    ]
    for c in numeric_cols:
        if c in df_fe.columns:
            df_fe[c] = pd.to_numeric(df_fe[c], errors="coerce")

    # =========================
    # 2) Features "taille" + morphologie
    # =========================
    # log surface
    if COL_GFA in df_fe.columns:
        df_fe["log_GFA"] = np.log(df_fe[COL_GFA].clip(lower=1))
    else:
        df_fe["log_GFA"] = np.nan

    # surface par bâtiment / par étage
    if COL_GFA in df_fe.columns and COL_BLDGS in df_fe.columns:
        df_fe["surface_per_building"] = df_fe[COL_GFA] / (df_fe[COL_BLDGS].clip(lower=1) + eps)
    else:
        df_fe["surface_per_building"] = np.nan

    if COL_GFA in df_fe.columns and COL_FLOOR in df_fe.columns:
        df_fe["surface_per_floor"] = df_fe[COL_GFA] / (df_fe[COL_FLOOR].clip(lower=1) + eps)
    else:
        df_fe["surface_per_floor"] = np.nan

    # parking
    if COL_PARK in df_fe.columns:
        df_fe["Has_Parking"] = (df_fe[COL_PARK].fillna(0) > 0).astype(int)
    else:
        df_fe["Has_Parking"] = np.nan

    if COL_PARK in df_fe.columns and COL_GFA in df_fe.columns:
        df_fe["Parking_share"] = df_fe[COL_PARK].fillna(0) / (df_fe[COL_GFA].clip(lower=1) + eps)
    else:
        df_fe["Parking_share"] = np.nan

    # =========================
    # 3) Features temporelles : Age + Era
    # =========================
    if COL_YEAR in df_fe.columns:
        year_series = pd.to_numeric(df_fe[COL_YEAR], errors="coerce")
        df_fe["Age"] = year_ref - year_series
        # cap simple (évite valeurs absurdes)
        df_fe.loc[df_fe["Age"] < 0, "Age"] = np.nan
        df_fe.loc[df_fe["Age"] > 200, "Age"] = np.nan

        y = year_series
        bins = [-np.inf, 1949, 1979, 1999, np.inf]
        labels = ["<1950", "1950-1980", "1980-2000", ">2000"]
        df_fe["Era"] = pd.cut(y, bins=bins, labels=labels)
    else:
        df_fe["Age"] = np.nan
        df_fe["Era"] = np.nan

    # =========================
    # 4) ENERGYSTAR (score + manquant informatif)
    # =========================
    if COL_ES in df_fe.columns:
        df_fe["Has_ENERGYSTAR"] = (~df_fe[COL_ES].isna()).astype(int)
        # log(Score) pas super utile ; on garde brut + indicateur
    else:
        df_fe["Has_ENERGYSTAR"] = 0

    # =========================
    # 5) Mix énergétique : kBtu + features robustes
    # =========================
    # On privilégie kBtu. Si pas dispo, on essaie de fallback proprement.
    elec = df_fe[COL_ELEC_KBTU] if COL_ELEC_KBTU in df_fe.columns else pd.Series(np.nan, index=df_fe.index)
    gas  = df_fe[COL_GAS_KBTU]  if COL_GAS_KBTU  in df_fe.columns else pd.Series(np.nan, index=df_fe.index)
    steam= df_fe[COL_STEAM]     if COL_STEAM     in df_fe.columns else pd.Series(np.nan, index=df_fe.index)

    # flags régime (plus robustes que ratios purs)
    if COL_GAS_KBTU in df_fe.columns:
        df_fe["Has_Gas"] = (gas.fillna(0) > 0).astype(int)
    else:
        df_fe["Has_Gas"] = np.nan

    if COL_STEAM in df_fe.columns:
        df_fe["Has_Steam"] = (steam.fillna(0) > 0).astype(int)
    else:
        df_fe["Has_Steam"] = np.nan

    # total energy from sources
    if COL_SITEN in df_fe.columns:
        total_energy = df_fe[COL_SITEN]
    else:
        total_energy = elec.fillna(0) + gas.fillna(0) + steam.fillna(0)

    df_fe["TotalEnergy_kBtu_proxy"] = total_energy

    # shares / ratios robustes
    df_fe["Fossil_kBtu"] = (gas.fillna(0) + steam.fillna(0))
    df_fe["Fossil_Ratio"] = df_fe["Fossil_kBtu"] / (df_fe["TotalEnergy_kBtu_proxy"].fillna(0) + 1.0)
    df_fe["Electrification_Rate"] = elec.fillna(0) / (df_fe["TotalEnergy_kBtu_proxy"].fillna(0) + 1.0)

    # intensités "physiques" (évite leakage : ici c’est énergie/surface, pas GHG/surface)
    if COL_GFA in df_fe.columns:
        df_fe["Energy_Intensity_kBtu_per_sqft"] = df_fe["TotalEnergy_kBtu_proxy"] / (df_fe[COL_GFA].clip(lower=1) + eps)
        df_fe["Fossil_Intensity_kBtu_per_sqft"] = df_fe["Fossil_kBtu"] / (df_fe[COL_GFA].clip(lower=1) + eps)
        df_fe["Electricity_Intensity_kBtu_per_sqft"] = elec.fillna(0) / (df_fe[COL_GFA].clip(lower=1) + eps)
        df_fe["Gas_Intensity_kBtu_per_sqft"] = gas.fillna(0) / (df_fe[COL_GFA].clip(lower=1) + eps)
        df_fe["Steam_Intensity_kBtu_per_sqft"] = steam.fillna(0) / (df_fe[COL_GFA].clip(lower=1) + eps)
    else:
        df_fe["Energy_Intensity_kBtu_per_sqft"] = np.nan
        df_fe["Fossil_Intensity_kBtu_per_sqft"] = np.nan
        df_fe["Electricity_Intensity_kBtu_per_sqft"] = np.nan
        df_fe["Gas_Intensity_kBtu_per_sqft"] = np.nan
        df_fe["Steam_Intensity_kBtu_per_sqft"] = np.nan

    # ratio gas/elec (secondaire)
    df_fe["Gas_to_Electricity_Ratio"] = gas.fillna(0) / (elec.fillna(0) + 1.0)
    df_fe["log_Gas_to_Electricity_Ratio"] = np.log1p(df_fe["Gas_to_Electricity_Ratio"])

    # logs utiles
    df_fe["log_TotalEnergy"] = np.log1p(df_fe["TotalEnergy_kBtu_proxy"].clip(lower=0))
    df_fe["log_Electricity_kBtu"] = np.log1p(elec.fillna(0))
    df_fe["log_Gas_kBtu"] = np.log1p(gas.fillna(0))
    df_fe["log_Steam_kBtu"] = np.log1p(steam.fillna(0))

    # =========================
    # 6) Interaction validée : Size_Intensity = GFA * EUI
    # =========================
    if (COL_GFA in df_fe.columns) and (COL_EUI in df_fe.columns):
        df_fe["Size_Intensity"] = df_fe[COL_GFA] * df_fe[COL_EUI]
    else:
        df_fe["Size_Intensity"] = np.nan

    # (optionnel, plutôt secondaire)
    if ("Age" in df_fe.columns) and (COL_ES in df_fe.columns):
        df_fe["Age_ENERGYSTAR"] = df_fe["Age"] * df_fe[COL_ES]
    else:
        df_fe["Age_ENERGYSTAR"] = np.nan

    # =========================
    # 7) Spatial simple
    # =========================
    if COL_NEI in df_fe.columns:
        df_fe["Is_Downtown"] = (df_fe[COL_NEI].astype(str).str.strip().str.upper() == "DOWNTOWN").astype(int)
    else:
        df_fe["Is_Downtown"] = np.nan

    # petit bonus robuste : “radius” depuis un centre (si tu ne l’as pas déjà)
    # centre approx downtown Seattle (Pioneer Square) — suffisant comme proxy
    if (COL_LAT in df_fe.columns) and (COL_LON in df_fe.columns):
        lat0, lon0 = 47.6038, -122.3301
        df_fe["distance_to_center_proxy"] = np.sqrt((df_fe[COL_LAT] - lat0)**2 + (df_fe[COL_LON] - lon0)**2)
    else:
        df_fe["distance_to_center_proxy"] = np.nan

    # =========================
    # 8) Nettoyage final (drop)
    # =========================
    cols_to_drop = [c for c in DROP_ALWAYS if c in df_fe.columns]

    if selection.drop_leaky:
        cols_to_drop += [c for c in DROP_LEAKY if c in df_fe.columns]

    # on drop les doublons d’unités si on garde les kBtu
    cols_to_drop += [c for c in DROP_UNIT_DUPLICATES if c in df_fe.columns]

    # si tu veux garder raw energy ou pas
    if not selection.keep_raw_energy:
        raw_energy = list(fe_cfg.raw_energy_cols)
        cols_to_drop += [c for c in raw_energy if c in df_fe.columns]

    # Important : on NE drop PAS la target ici (utile pour split train/test),
    # mais si tu veux X prêt, tu feras X = df_fe.drop(columns=[COL_TARGET])
    df_fe = df_fe.drop(columns=list(dict.fromkeys(cols_to_drop)), errors="ignore")

    # Nettoyage des résidus de nettoyage (piloté par config)
    df_fe = df_fe.drop(columns=[c for c in fe_cfg.drop_list if c in df_fe.columns], errors="ignore")

    # Harmonisation des flags pour réduire la mémoire
    for col in fe_cfg.flag_cols:
        if col in df_fe.columns:
            df_fe[col] = df_fe[col].fillna(0).astype("uint8")

    # Allow-list finale
    if selection.final_features_only:
        final_features = [c for c in fe_cfg.final_features if c in df_fe.columns]
        df_fe = df_fe.loc[:, final_features]

    save_feature_engineering_output(df_fe, cfg)
    return df_fe


def save_feature_engineering_output(df: pd.DataFrame, cfg) -> Path:
    output_dir = Path(cfg.feature_engineering.output.dir)
    if not output_dir.is_absolute():
        output_dir = (PROJECT_ROOT / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = cfg.feature_engineering.output.file
    output_path = output_dir / filename
    df.to_csv(output_path, index=False)
    meta_path = output_dir / f"{Path(filename).stem}_metadata.json"
    meta_payload = {
        "timestamp": datetime.now().isoformat(),
        "rows": int(len(df)),
        "cols": int(df.shape[1]),
        "file": str(output_path),
        "metadata": cfg.feature_engineering.metadata or {},
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=4, ensure_ascii=False)
    print(f"✓ Feature engineering sauvegarde dans : {output_path}")
    return output_path
