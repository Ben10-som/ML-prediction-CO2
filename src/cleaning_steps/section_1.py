import pandas as pd
import numpy as np
from .base_processor import BaseCleaner
import warnings

class Section1(BaseCleaner):
    def run(self, df):
        df = df.copy()
        s1_cfg = self.cfg.cleaning.section_1
        s2_cols = self.cfg.cleaning.section_2.columns
        audit_details = {}

        # 1. SÉCURITÉ ET SUPPRESSION EXPLICITE DES OUTLIERS MARQUÉS
        if "exclusion_reason" not in df.columns:
            df["exclusion_reason"] = None

        if 'Outlier' in df.columns:
            mask_already_outlier = df['Outlier'].notna() & (df['Outlier'] != "") & (df['Outlier'] != 0)
            df.loc[mask_already_outlier, "exclusion_reason"] = "Pre-marked Outlier"

        mask_non_compliant = df['ComplianceStatus'] != s1_cfg.compliance_value
        df.loc[mask_non_compliant, "exclusion_reason"] = "Non-Compliant Status"
        
        mask_to_remove = df["exclusion_reason"].notna()
        df_step1 = df[~mask_to_remove].copy()
        audit_details["total_rows_rejected"] = int(mask_to_remove.sum())

        # 2. FEATURE ENGINEERING (FLAGS D'ABSENCE)
        usage_col = s2_cols.primary_usage
        df_step1['IsMixedUse'] = df_step1['SecondLargestPropertyUseType'].notna().astype(int)
        
        if 'ENERGYSTARScore' in df_step1.columns:
            df_step1['Has_EnergyStarScore'] = df_step1['ENERGYSTARScore'].notna().astype(int)

        # 3. IMPUTATIONS EN CASCADE (Usage -> Global)
        missing_pct = df_step1.isnull().mean()
        cols_to_impute = missing_pct[(missing_pct > 0) & (df_step1.dtypes != 'object')].index.tolist()
        
        # On encapsule ici pour ignorer les warnings de médiane sur tranches vides
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Mean of empty slice")
            
            for col in cols_to_impute:
                # Cascade : Médiane par usage, puis médiane globale
                df_step1[col] = df_step1.groupby(usage_col)[col].transform(lambda x: x.fillna(x.median()))
                df_step1[col] = df_step1[col].fillna(df_step1[col].median())
                
                if col == s2_cols.floors:
                    df_step1[col] = df_step1[col].round().astype(int)

        # 4. FILTRE DE VACUITÉ FINALE
        row_missing_pct = df_step1.isnull().mean(axis=1)
        mask_too_many_missing = row_missing_pct > s1_cfg.thresholds.row_max_missing_pct
        
        df.loc[df_step1.index[mask_too_many_missing], "exclusion_reason"] = "Excessive Missing Data"
        df_final = df_step1[~mask_too_many_missing].copy()

        # 5. AUDIT ET NETTOYAGE COLONNES
        self.audit(df, df_final, audit_details)
        
        return df_final