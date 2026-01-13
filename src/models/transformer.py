import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler, FunctionTransformer

class GroupMedianImputer(BaseEstimator, TransformerMixin):
    def __init__(self, group_col: str, min_group_size: int = 1):
        self.group_col = group_col
        self.min_group_size = min_group_size
        self.integer_cols_ = []

    def fit(self, X: pd.DataFrame, y=None):
        if self.group_col not in X.columns:
            raise ValueError(f"{self.group_col} absent dans X lors de fit()")
        
        # FIX: On s'assure d'extraire une Series, même si la colonne est présente en double
        group_series = X[self.group_col]
        if isinstance(group_series, pd.DataFrame):
            group_series = group_series.iloc[:, 0]

        numeric_cols = X.select_dtypes(include="number").columns
        self.integer_cols_ = []
        for col in numeric_cols:
            non_na_values = X[col].dropna()
            if not non_na_values.empty and (non_na_values % 1 == 0).all():
                self.integer_cols_.append(col)

        # Utilisation de la Series extraite pour le groupby
        group_counts = X.groupby(group_series).size()
        medians = X.groupby(group_series).median(numeric_only=True)

        for g, cnt in group_counts.items():
            if cnt < self.min_group_size and g in medians.index:
                medians.loc[g, :] = np.nan
        
        self.group_medians_ = medians
        self.global_median_ = X.median(numeric_only=True)
        return self

    def transform(self, X: pd.DataFrame):
        X = X.copy()
        group_series = X[self.group_col]
        if isinstance(group_series, pd.DataFrame):
            group_series = group_series.iloc[:, 0]

        for col in self.group_medians_.columns:
            if col not in X.columns:
                continue
            X[col] = X[col].fillna(group_series.map(self.group_medians_[col]))
            X[col] = X[col].fillna(self.global_median_[col])
            
            if col in self.integer_cols_:
                X[col] = np.ceil(X[col]).astype(int)
                
        return X.drop(columns=[self.group_col], errors="ignore")

class GroupModeImputer(BaseEstimator, TransformerMixin):
    def __init__(self, group_col: str, categorical_cols=None, min_group_size: int = 1):
        self.group_col = group_col
        self.categorical_cols = categorical_cols
        self.min_group_size = min_group_size

    def fit(self, X: pd.DataFrame, y=None):
        group_series = X[self.group_col]
        if isinstance(group_series, pd.DataFrame):
            group_series = group_series.iloc[:, 0]

        if self.categorical_cols is None:
            self.categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
            if self.group_col in self.categorical_cols:
                self.categorical_cols.remove(self.group_col)

        group_counts = X.groupby(group_series).size()
        self.group_modes_ = {}
        for col in self.categorical_cols:
            # Agrégation robuste pour le mode
            modes = X.groupby(group_series)[col].apply(
                lambda s: s.mode().iloc[0] if not s.mode().empty else None
            )
            for g, cnt in group_counts.items():
                if cnt < self.min_group_size and g in modes.index:
                    modes.loc[g] = None
            self.group_modes_[col] = modes
        
        self.global_modes_ = {col: X[col].mode().iloc[0] if not X[col].mode().empty else None 
                             for col in self.categorical_cols}
        return self

    def transform(self, X: pd.DataFrame):
        X = X.copy()
        group_series = X[self.group_col]
        if isinstance(group_series, pd.DataFrame):
            group_series = group_series.iloc[:, 0]

        for col in self.categorical_cols:
            if col not in X.columns:
                continue
            X[col] = X[col].fillna(group_series.map(self.group_modes_.get(col, pd.Series(dtype='object'))))
            X[col] = X[col].fillna(self.global_modes_.get(col))
        return X

def make_preprocessor(num_cols, cat_cols, binary_cols, numeric_scaler="robust", min_group_size=1, ohe_sparse_output=False):
    GROUP_COL = "PrimaryPropertyType"
    
    # Sécurité : on retire GROUP_COL des listes si jamais il y est déjà
    num_cols = [c for c in num_cols if c != GROUP_COL]
    cat_cols = [c for c in cat_cols if c != GROUP_COL]

    scaler_map = {
        "robust": RobustScaler(),
        "standard": StandardScaler(),
        "none": "passthrough",
        None: "passthrough",
    }
    scaler = scaler_map.get(numeric_scaler, "passthrough")

    numeric_pipeline = Pipeline([
        ("imputer", GroupMedianImputer(group_col=GROUP_COL, min_group_size=min_group_size)),
        ("scaler", scaler if scaler != "passthrough" else FunctionTransformer(lambda x: x))
    ])

    categorical_pipeline = Pipeline([
    ("imputer", GroupModeImputer(group_col=GROUP_COL, categorical_cols=cat_cols, min_group_size=min_group_size)),
    ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=ohe_sparse_output)),
    ])


    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, [GROUP_COL] + num_cols),
            ("cat", categorical_pipeline, [GROUP_COL] + cat_cols),
            ("bin", "passthrough", binary_cols),
        ],
        remainder="drop",
    )
    return preprocessor