import pandas as pd
import numpy as np
from .base_processor import BaseCleaner

class Section1(BaseCleaner):
    def run(self, df):
        # On travaille sur une copie pour enrichir le CSV removed
        df = df.copy()
        df_before = df.copy()
        s1_cfg = self.cfg.cleaning.section_1
        audit_details = {}

        # Initialisation de la colonne de diagnostic pour le CSV removed
        df["exclusion_reason"] = None

        # 1. Marquage Compliance
        mask_non_compliant = df['ComplianceStatus'] != s1_cfg.compliance_value
        df.loc[mask_non_compliant, "exclusion_reason"] = "Non-Compliant Status"
        
        # On applique le premier filtre (obligatoire avant l'imputation)
        df_step1 = df[~mask_non_compliant].copy()
        audit_details["rows_non_compliant_removed"] = int(mask_non_compliant.sum())

        # 2. Suppression colonnes techniques
        df_step1 = df_step1.drop(columns=[c for c in s1_cfg.cols_to_drop if c in df_step1.columns])
        
        # 3. Feature Engineering (Flags)
        df_step1['IsMixedUse'] = df_step1['SecondLargestPropertyUseType'].notna().astype(int)
        df_step1['Has_EnergyStarScore'] = df_step1['ENERGYSTARScore'].notna().astype(int)
        df_step1 = df_step1.drop(columns=['SecondLargestPropertyUseType', 'SecondLargestPropertyUseTypeGFA'], errors='ignore')

        # 4. Identification des colonnes pour imputation
        missing_pct = df_step1.isnull().mean()
        low_miss_limit = s1_cfg.thresholds.low_missing_pct
        cols_to_impute = missing_pct[(missing_pct > 0) & (missing_pct < low_miss_limit)].index.tolist()
        if 'ENERGYSTARScore' not in cols_to_impute:
            cols_to_impute.append('ENERGYSTARScore')

        # 5. Imputation par groupe
        for col in cols_to_impute:
            if df_step1[col].dtype in ['float64', 'int64']:
                global_median = df_step1[col].median()
                df_step1[col] = df_step1.groupby('PrimaryPropertyType')[col].transform(lambda x: x.fillna(x.median()))
                df_step1[col] = df_step1[col].fillna(global_median)
            else:
                global_mode = df_step1[col].mode()[0] if not df_step1[col].mode().empty else np.nan
                df_step1[col] = df_step1.groupby('PrimaryPropertyType')[col].transform(
                    lambda x: x.fillna(x.mode()[0] if not x.mode().empty else np.nan)
                )
                df_step1[col] = df_step1[col].fillna(global_mode)

        # 6. Marquage et Suppression lignes (Missing > X%)
        row_missing_pct = df_step1.isnull().mean(axis=1)
        max_row_limit = s1_cfg.thresholds.row_max_missing_pct
        mask_too_many_missing = row_missing_pct > max_row_limit
        
        # On reporte l'info dans le df original pour l'audit
        df.loc[df_step1.index[mask_too_many_missing], "exclusion_reason"] = f"Excessive Missing Data (>{max_row_limit*100}%)"
        
        df_after = df_step1[~mask_too_many_missing].copy()
        audit_details["rows_excessive_missing_removed"] = int(mask_too_many_missing.sum())

        # 7. Audit Final
        # En passant 'df', le CSV 'Section1_removed.csv' contiendra la colonne 'exclusion_reason'
        self.audit(df, df_after, audit_details)
        
        return df_after