import pandas as pd
import numpy as np
from .base_processor import BaseCleaner
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")

class Section3(BaseCleaner):
    def run(self, df):
        df = df.copy()
        df_before = df.copy()
        s3_cfg = self.cfg.cleaning.section_3
        audit = {}
        df["exclusion_reason"] = None

        # 1. Restauration de la vérité physique
        mask_wn_zero = (df['SiteEnergyUse(kBtu)'] > 0) & (df['SiteEnergyUseWN(kBtu)'] == 0)
        df.loc[mask_wn_zero, 'SiteEnergyUseWN(kBtu)'] = df.loc[mask_wn_zero, 'SiteEnergyUse(kBtu)']

        # 2. Recalcul des intensités (EUI)
        surface_col = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else 'PropertyGFATotal'
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_col]
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEUIWN(kBtu/sf)'].fillna(0)

        # 3. Détection IQR (Calcul des drapeaux)
        # On s'assure que TotalGHGEmissions est traité même s'il est oublié dans le YAML
        vars_to_process = list(set(s3_cfg.iqr_vars + ['TotalGHGEmissions']))
        
        for col in vars_to_process:
            if col not in df.columns: continue 
            
            def get_iqr_flags(group, multiplier=3.0):
                clean_group = group.dropna()
                if len(clean_group) < 2: return pd.Series(False, index=group.index)
                q1, q3 = clean_group.quantile(0.25), clean_group.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0: return pd.Series(False, index=group.index)
                return (group < (q1 - multiplier * iqr)) | (group > (q3 + multiplier * iqr))

            df[f"is_outlier_iqr_{col}"] = df.groupby('PrimaryPropertyType')[col].transform(lambda x: get_iqr_flags(x, 3.0)).astype(int)
            df[f"is_extreme_5iqr_{col}"] = df.groupby('PrimaryPropertyType')[col].transform(lambda x: get_iqr_flags(x, 5.0)).astype(int)

        # 4. Logique de décision Avancée
        # Utilisation de .get() pour éviter les KeyError si une colonne manque
        mask_outlier_eui = (df.get('is_outlier_iqr_SiteEUI(kBtu/sf)', 0) == 1)
        mask_outlier_target = (df.get('is_outlier_iqr_TotalGHGEmissions', 0) == 1)
        
        # Avocats de la défense
        mask_justified_size = (df.get('is_outlier_iqr_PropertyGFATotal', 0) == 1)
        mask_high_performer = (df.get('ENERGYSTARScore', 0) >= 70)
        
        # Garde-fou 5.0 IQR
        mask_unjustifiable = (df.get('is_extreme_5iqr_SiteEUI(kBtu/sf)', 0) == 1) | \
                             (df.get('is_extreme_5iqr_TotalGHGEmissions', 0) == 1)

        # Application de la sentence
        mask_drop = (mask_outlier_eui | mask_outlier_target) & (~mask_justified_size) & (~mask_high_performer)
        mask_drop = mask_drop | mask_unjustifiable

        # Marquage
        df.loc[mask_unjustifiable, "exclusion_reason"] = "Critical Outlier (> 5.0 IQR)"
        df.loc[mask_drop & df["exclusion_reason"].isna(), "exclusion_reason"] = "Standard Outlier (No justification)"

        # 5. Application et Audit
        df_after = df[~mask_drop].copy()
        
        audit["total_removed"] = int(mask_drop.sum())
        audit["critical_errors_removed"] = int(mask_unjustifiable.sum())
        audit["saved_by_context"] = int(((mask_outlier_eui | mask_outlier_target) & ~mask_unjustifiable & (mask_justified_size | mask_high_performer)).sum())

        # Nettoyage des colonnes temporaires
        cols_to_drop = [c for c in df_after.columns if "is_outlier_iqr_" in c or "is_extreme_5iqr_" in c or "exclusion_reason" in c]
        df_final = df_after.drop(columns=cols_to_drop)
        
        self.audit(df, df_final, audit)
        return df_final