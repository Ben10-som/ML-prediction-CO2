import pandas as pd
import numpy as np
from .base_processor import BaseCleaner

class Section1(BaseCleaner):
    def run(self, df):
        df_before = df.copy()
        s1_cfg = self.cfg.cleaning.section_1
        audit_details = {}

        # 1. Filtrage Compliance
        initial_count = len(df)
        df = df[df['ComplianceStatus'] == s1_cfg.compliance_value].copy()
        audit_details["rows_non_compliant_removed"] = initial_count - len(df)

        # 2. Suppression colonnes
        df = df.drop(columns=[c for c in s1_cfg.cols_to_drop if c in df.columns])
        
        # 3. Mixed Use & EnergyStar Flags
        df['IsMixedUse'] = df['SecondLargestPropertyUseType'].notna().astype(int)
        df['Has_EnergyStarScore'] = df['ENERGYSTARScore'].notna().astype(int)
        df = df.drop(columns=['SecondLargestPropertyUseType', 'SecondLargestPropertyUseTypeGFA'], errors='ignore')

        # 4. Identification des colonnes pour imputation (< X%)
        missing_pct = df.isnull().mean()
        low_miss_limit = s1_cfg.thresholds.low_missing_pct
        
        cols_to_impute = missing_pct[(missing_pct > 0) & (missing_pct < low_miss_limit)].index.tolist()
        if 'ENERGYSTARScore' not in cols_to_impute:
            cols_to_impute.append('ENERGYSTARScore')

        # 5. Imputation par groupe (Médiane pour num, Mode pour cat)
        for col in cols_to_impute:
            if df[col].dtype in ['float64', 'int64']:
                # Calcul de la médiane globale de secours au préalable
                global_median = df[col].median()
                
                df[col] = df.groupby('PrimaryPropertyType')[col].transform(
                    lambda x: x.fillna(x.median())
                )
                # Sécurité finale : si un groupe entier était vide, on finit à la médiane globale
                df[col] = df[col].fillna(global_median)
                
            else:
                # Calcul du mode global de secours
                global_mode = df[col].mode()[0] if not df[col].mode().empty else np.nan
                
                df[col] = df.groupby('PrimaryPropertyType')[col].transform(
                    lambda x: x.fillna(x.mode()[0] if not x.mode().empty else np.nan)
                )
                df[col] = df[col].fillna(global_mode)

        # 6. Suppression lignes (Missing > X%)
        row_missing_pct = df.isnull().mean(axis=1)
        max_row_limit = s1_cfg.thresholds.row_max_missing_pct
        mask_too_many_missing = row_missing_pct > max_row_limit
        df = df[~mask_too_many_missing].copy()
        
        audit_details["rows_excessive_missing_removed"] = int(mask_too_many_missing.sum())

        self.audit(df_before, df, audit_details)
        return df