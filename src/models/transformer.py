
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler


class GroupMedianImputer(BaseEstimator, TransformerMixin):
    def __init__(self, group_col: str, min_group_size: int = 1):
        self.group_col = group_col
        self.min_group_size = min_group_size
        self.integer_cols_ = [] # Pour stocker les colonnes qui doivent être arrondies

    def fit(self, X: pd.DataFrame, y=None):
        if self.group_col not in X.columns:
            raise ValueError(f"{self.group_col} absent dans X lors de fit()")
        
        # Identifier les colonnes numériques
        numeric_cols = X.select_dtypes(include="number").columns
        
        # Détecter les colonnes "purement entières" (ex: 1.0, 2.0, NaN)
        self.integer_cols_ = []
        for col in numeric_cols:
            non_na_values = X[col].dropna()
            if not non_na_values.empty and (non_na_values % 1 == 0).all():
                self.integer_cols_.append(col)

        # Compter et calculer médianes par groupe
        group_counts = X.groupby(self.group_col).size()
        medians = X.groupby(self.group_col).median(numeric_only=True)

        for g, cnt in group_counts.items():
            if cnt < self.min_group_size and g in medians.index:
                medians.loc[g, :] = np.nan
        
        self.group_medians_ = medians
        self.global_median_ = X.median(numeric_only=True)
        return self

    def transform(self, X: pd.DataFrame):
        X = X.copy()
        for col in self.group_medians_.columns:
            if col not in X.columns:
                continue
            
            # Imputation par groupe puis globale
            X[col] = X[col].fillna(X[self.group_col].map(self.group_medians_[col]))
            X[col] = X[col].fillna(self.global_median_[col])
            
            # Si la colonne était initialement composée d'entiers, on arrondit au supérieur
            if col in self.integer_cols_:
                X[col] = np.ceil(X[col]).astype(int)
                
        return X.drop(columns=[self.group_col], errors="ignore")

class GroupModeImputer(BaseEstimator, TransformerMixin):
    def __init__(self, group_col: str, categorical_cols=None, min_group_size: int = 1):
        # ne pas transformer categorical_cols ici 
        self.group_col = group_col
        self.categorical_cols = categorical_cols  # peut être None ; on infère dans fit()
        self.min_group_size = min_group_size

    def fit(self, X: pd.DataFrame, y=None):
        if self.group_col not in X.columns:
            raise ValueError(f"{self.group_col} absent dans X lors de fit()")
        # si categorical_cols n'est pas fourni, inférer toutes les colonnes de type object/category
        if self.categorical_cols is None:
            self.categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
        # calculer mode par groupe
        group_counts = X.groupby(self.group_col).size()
        self.group_modes_ = {}
        for col in self.categorical_cols:
            modes = X.groupby(self.group_col)[col].agg(
                lambda s: s.mode().iloc[0] if not s.mode().empty else None
            )
            for g, cnt in group_counts.items():
                if cnt < self.min_group_size and g in modes.index:
                    modes.loc[g] = None
            self.group_modes_[col] = modes
        # global modes fallback
        self.global_modes_ = {col: X[col].mode().iloc[0] for col in self.categorical_cols}
        return self

    def transform(self, X: pd.DataFrame):
        X = X.copy()
        for col in self.categorical_cols:
            if col not in X.columns:
                continue
            X[col] = X[col].fillna(X[self.group_col].map(self.group_modes_.get(col, pd.Series())))
            X[col] = X[col].fillna(self.global_modes_.get(col))
        # conserver la colonne de regroupement avant l'encodeur
        return X


def make_preprocessor(
    num_cols,
    cat_cols,
    binary_cols,
    group_col,
    categorical_features,
    numeric_scaler="robust",
    min_group_size=1,
    ohe_sparse_output=False,
):
    scaler_map = {
        "robust": RobustScaler(),
        "standard": StandardScaler(),
        "none": "passthrough",
        None: "passthrough",
    }
    if numeric_scaler not in scaler_map:
        raise ValueError(f"numeric_scaler invalide: {numeric_scaler}")
    scaler = scaler_map[numeric_scaler]

    numeric_steps = [
        ("imputer", GroupMedianImputer(group_col=group_col, min_group_size=min_group_size)),
    ]
    if scaler != "passthrough":
        numeric_steps.append(("scaler", scaler))

    numeric_pipeline = Pipeline(numeric_steps)
    categorical_pipeline = Pipeline([
        ("imputer", GroupModeImputer(group_col=group_col, categorical_cols=categorical_features, min_group_size=min_group_size)),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=ohe_sparse_output)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, [group_col] + num_cols),
            ("bin", "passthrough", binary_cols),
            ("cat", categorical_pipeline, cat_cols),
        ],
        remainder="drop",
    )
    return preprocessor