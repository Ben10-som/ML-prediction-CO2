import pandas as pd
import numpy as np
from scipy import stats
from .base_processor import BaseCleaner

class Section3(BaseCleaner):
    def run(self, df):
        df = df.copy()
        s3_cfg = self.cfg.cleaning.section_3
        t = s3_cfg.thresholds
        audit = {}
        df["exclusion_reason"] = None

        # 1. Préparation des variables (WN déjà synchronisées en S2)
        # On s'assure que les colonnes calculées comme SiteEUIWN existent
        surface_col = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else 'PropertyGFATotal'
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_col]

        # 2. DÉTECTION PAR Z-SCORE (Variables de volume)
        zscore_cols = [c for c in s3_cfg.zscore_vars if c in df.columns]
        for col in zscore_cols:
            # Calcul du Z-Score par groupe d'usage pour ne pas biaiser les stats
            df[f'zscore_{col}'] = df.groupby('PrimaryPropertyType')[col].transform(
                lambda x: stats.zscore(x, nan_policy='omit') if x.count() > 5 else 0
            )

        # 3. DÉTECTION PAR IQR (Variables de structure/intensité)
        iqr_cols = [c for c in s3_cfg.iqr_vars if c in df.columns]
        for col in iqr_cols:
            def get_iqr_outliers(group):
                q1, q3 = group.quantile(0.25), group.quantile(0.75)
                iqr = q3 - q1
                return (group < (q1 - t.iqr_multiplier * iqr)) | (group > (q3 + t.iqr_multiplier * iqr))
            
            df[f'is_iqr_outlier_{col}'] = df.groupby('PrimaryPropertyType')[col].transform(
                lambda x: get_iqr_outliers(x) if x.count() > 5 else False
            ).astype(int)

        # 4. LOGIQUE D'EXCLUSION SELON TES SEUILS
        # A. Trop de Z-Scores élevés sur une seule ligne
        zscore_flag_cols = [f'zscore_{c}' for c in zscore_cols]
        df['extreme_zscore_count'] = (df[zscore_flag_cols].abs() > t.zscore_limit).sum(axis=1)
        
        mask_zscore_limit = df['extreme_zscore_count'] >= t.zscore_sum_limit

        # B. Outliers IQR sur les variables critiques (EUI et Surface)
        mask_iqr_critical = (df.get('is_iqr_outlier_SiteEUI(kBtu/sf)', 0) == 1) | \
                            (df.get('is_iqr_outlier_PropertyGFATotal', 0) == 1)

        # C. Exemption pour les structures massives (University, Hospital, etc.)
        mask_massive = df['PrimaryPropertyType'].isin(s3_cfg.massive_structures_types)

        # APPLICATION DE LA SENTENCE
        # On supprime si (Zscore excessif OU IQR critique) ET que ce n'est pas une structure massive
        mask_drop = (mask_zscore_limit | mask_iqr_critical) & (~mask_massive)

        # Marquage pour l'audit
        df.loc[mask_zscore_limit, "exclusion_reason"] = f"ZScore Sum > {t.zscore_sum_limit}"
        df.loc[mask_iqr_critical & df["exclusion_reason"].isna(), "exclusion_reason"] = "Critical IQR Outlier"
        
        # 5. NETTOYAGE ET AUDIT
        df_after = df[~mask_drop].copy()
        
        # On garde 'extreme_zscore_count' comme feature pour le ML, on drop le reste
        cols_to_drop = [c for c in df.columns if ('zscore_' in c or 'is_iqr_' in c) and c != 'extreme_zscore_count']
        df_final = df_after.drop(columns=cols_to_drop + ["exclusion_reason"], errors='ignore')

        audit.update({
            "rows_removed_zscore": int(mask_zscore_limit.sum()),
            "rows_removed_iqr": int(mask_iqr_critical.sum()),
            "massive_structures_preserved": int((mask_massive & (mask_zscore_limit | mask_iqr_critical)).sum()),
            "total_section3_removed": int(mask_drop.sum())
        })

        self.audit(df, df_final, audit)
        return df_final