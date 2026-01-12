from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from datetime import datetime
import json
from fastapi.middleware.cors import CORSMiddleware


# ----------------------
# Chemins vers dossiers
# ----------------------
base = Path(__file__).resolve().parent.parent  # remonte à dashboard/
model_path = base / "models" / "co2_model.joblib"
data_folder = base / "data"
predictions_file = data_folder / "predictions.json"

# ----------------------
# Charger ou créer modèle
# ----------------------
if model_path.exists():
    model = joblib.load(model_path)
else:
    model = LinearRegression()

# ----------------------
# FastAPI
# ----------------------
app = FastAPI(title="CO2 Emissions Prediction API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # pour dev
allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# ----------------------
# Pydantic pour validation des entrées
# ----------------------
class CO2Input(BaseModel):
    # Features Front (User Input)
    NumberofFloors: int
    NumberofBuildings: int
    Age: float
    ENERGYSTARScore: float = None  # Optionnel
    PrimaryPropertyType: str
    BuildingType: str
    Neighborhood: str
    Latitude: float
    Longitude: float
    Has_Parking: int = 0
    Has_Gas: int = 0
    Has_Steam: int = 0
    
    # Hidden / Optional for calculations (if passed by advanced front, else NaN/Imputed)
    PropertyGFATotal: float = None 
    PropertyGFAParking: float = None

# ----------------------
# Fonction Feature Engineering (Backend)
# ----------------------
def calculate_features(input_data: CO2Input):
    data = input_data.dict()
    
    # 1. Recuperation inputs
    gfa = data.get("PropertyGFATotal")
    if gfa is None: gfa = np.nan
    
    # 2. YearRef / Age
    # L'utilisateur saisit l'Age directement, donc pas besoin de YearBuilt
    age = data.get("Age")

    # 3. Spatial
    lat = data.get("Latitude")
    lon = data.get("Longitude")
    lat0, lon0 = 47.6038, -122.3301
    
    dist_proxy = np.sqrt((lat - lat0)**2 + (lon - lon0)**2)
    
    neighborhood = str(data.get("Neighborhood")).strip().upper()
    is_downtown = 1 if neighborhood == "DOWNTOWN" else 0
    
    # 4. Energy Star
    es_score = data.get("ENERGYSTARScore")
    if es_score is None or np.isnan(es_score):
        has_energystar = 0
        age_energystar = np.nan
        # Pour le pipeline scikit-learn, il faut peut-etre une valeur numerique pour Score
        # Si le pipeline a un imputer, np.nan suffit.
    else:
        has_energystar = 1
        age_energystar = age * es_score

    # 5. Surfaces / Morpho
    eps = 1e-6
    if not np.isnan(gfa):
        log_gfa = np.log(max(gfa, 1))
        
        n_bldgs = data.get("NumberofBuildings")
        surf_per_bldg = gfa / (max(n_bldgs, 1) + eps)
        
        n_floors = data.get("NumberofFloors")
        surf_per_floor = gfa / (max(n_floors, 1) + eps)
        
        park_gfa = data.get("PropertyGFAParking")
        if park_gfa is None: park_gfa = 0 # ou np.nan
        # Si Has_Parking=0, on suppose park_gfa=0
        if data.get("Has_Parking") == 0:
            park_gfa = 0
            
        parking_share = park_gfa / (gfa + eps)
    else:
        log_gfa = np.nan
        surf_per_bldg = np.nan
        surf_per_floor = np.nan
        parking_share = np.nan

    # Construction du dictionnaire final pour le DataFrame
    # Doit matcher les colonnes attendues par le pipeline (train)
    
    features = {
        "NumberofFloors": data.get("NumberofFloors"),
        "NumberofBuildings": data.get("NumberofBuildings"),
        "Age": age,
        "ENERGYSTARScore": es_score,
        "PrimaryPropertyType": data.get("PrimaryPropertyType"),
        "BuildingType": data.get("BuildingType"),
        "Neighborhood": data.get("Neighborhood"),
        "Latitude": lat,
        "Longitude": lon,
        "Is_Downtown": is_downtown,
        "distance_to_center_proxy": dist_proxy,
        "log_GFA": log_gfa,
        "surface_per_building": surf_per_bldg,
        "surface_per_floor": surf_per_floor,
        "Has_Parking": data.get("Has_Parking"),
        "Parking_share": parking_share,
        "Has_ENERGYSTAR": has_energystar,
        "Has_Gas": data.get("Has_Gas"),
        "Has_Steam": data.get("Has_Steam"),
        "Age_ENERGYSTAR": age_energystar
    }
    
    return features

# ----------------------
# Fonction pour sauvegarder une prédiction dans JSON
# ----------------------
def save_prediction_json(data_dict, predicted_CO2):
    row = data_dict.copy()
    row["predicted_CO2"] = predicted_CO2
    row["timestamp"] = datetime.utcnow().isoformat()

    if predictions_file.exists():
        with open(predictions_file, 'r') as f:
            all_preds = json.load(f)
    else:
        all_preds = []

    all_preds.append(row)

    with open(predictions_file, 'w') as f:
        json.dump(all_preds, f, indent=4)

# ----------------------
# Endpoints
# ----------------------
@app.get("/")
def home():
    return {"message": "API CO2 is running 🚀"}

@app.post("/predict")
def predict(input_data: CO2Input):
    # 1. Calcul des features backend
    computed_features = calculate_features(input_data)
    
    # 2. Creation DataFrame
    df = pd.DataFrame([computed_features])
    
    try:
        prediction = model.predict(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur prédiction: {str(e)}")

    pred_value = float(prediction[0])
    # On sauvegarde l'input brut + la pred
    save_prediction_json(input_data.dict(), pred_value)

    return {"prediction_CO2": pred_value}

@app.get("/data")
def get_data(limit: int = 100):
    if not predictions_file.exists():
        return {"predictions": []}
    with open(predictions_file, 'r') as f:
        all_preds = json.load(f)
    # Retourner les dernières prédictions
    return {"predictions": all_preds[-limit:]}

@app.get("/metrics")
def metrics():
    if not predictions_file.exists():
        return {"total_predictions": 0, "average_CO2": None}
    with open(predictions_file, 'r') as f:
        all_preds = json.load(f)
    total = len(all_preds)
    avg = sum(pred["predicted_CO2"] for pred in all_preds) / total
    return {"total_predictions": total, "average_CO2": avg}

@app.get("/health")
def health():
    try:
        model_status = model is not None
        return {"status": "ok" if model_status else "error", "model_loaded": model_status}
    except:
        return {"status": "error", "model_loaded": False}

@app.post("/retrain")
def retrain():
    try:
        # Lire tous les CSV du dossier data
        all_files = list(data_folder.glob("*.csv"))
        if not all_files:
            raise HTTPException(status_code=400, detail="Aucun fichier CSV trouvé dans data/")

        df_list = [pd.read_csv(f) for f in all_files]
        data = pd.concat(df_list, ignore_index=True)

        # Liste des features
        numeric_features = [
            "NumberofFloors", "NumberofBuildings", "Age", "ENERGYSTARScore",
            "Latitude", "Longitude", "Is_Downtown", "distance_to_center_proxy",
            "log_GFA", "surface_per_building", "surface_per_floor",
            "Has_Parking", "Parking_share", "Has_ENERGYSTAR",
            "Has_Gas", "Has_Steam", "Age_ENERGYSTAR"
        ]
        categorical_features = ["PrimaryPropertyType", "BuildingType", "Neighborhood"]

        X_cols = numeric_features + categorical_features
        y_col = "TotalGHGEmissions"

        # Vérification si les colonnes existent
        missing_cols = [c for c in X_cols + [y_col] if c not in data.columns]
        if missing_cols:
             raise HTTPException(status_code=400, detail=f"Colonnes manquantes dans le CSV : {missing_cols}")

        X = data[X_cols]
        y = data[y_col]

        # Pipeline de prétraitement
        numeric_transformer = make_pipeline(
            SimpleImputer(strategy='median'),
            StandardScaler()
        )

        categorical_transformer = make_pipeline(
            SimpleImputer(strategy='constant', fill_value='missing'),
            OneHotEncoder(handle_unknown='ignore')
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', categorical_transformer, categorical_features)
            ]
        )

        global model
        model = make_pipeline(preprocessor, LinearRegression())
        model.fit(X, y)

        # Sauvegarde du modèle
        joblib.dump(model, model_path)

        return {"status": "ok", "message": "Modèle réentraîné avec succès à partir des CSV"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur retrain: {str(e)}")


@app.get("/data-raw")
def get_raw_data():
    df = pd.read_csv(base / "data" / "data_cleaned.csv")
    
    # Remplacer les NaN par une valeur acceptable pour JSON
    df = df.fillna("")  # ici on met une chaîne vide, tu peux aussi mettre 0 si c’est numérique

    # Convertir tous les types en Python natif pour éviter les float64 etc.
    data_dict = df.astype(object).to_dict(orient="records")
    return {"raw_data": data_dict}
