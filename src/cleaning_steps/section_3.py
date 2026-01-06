import pandas as pd
import numpy as np
from .base_processor import BaseCleaner
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")

class Section3(BaseCleaner):
    def run(self, df):
        df_before = df.copy()
        s3_cfg = self.cfg.cleaning.section_3
        audit = {}

        # 1. Restauration de la vérité physique (Weather Normalized)
        mask_wn_zero = (df['SiteEnergyUse(kBtu)'] > 0) & (df['SiteEnergyUseWN(kBtu)'] == 0)
        df.loc[mask_wn_zero, 'SiteEnergyUseWN(kBtu)'] = df.loc[mask_wn_zero, 'SiteEnergyUse(kBtu)']
        audit["corrections_energy_wn_zero"] = int(mask_wn_zero.sum())

        # 2. Recalcul des indicateurs d'intensité (EUI)
        # On utilise PropertyGFABuilding(s) pour la précision thermique si disponible
        surface_col = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else 'PropertyGFATotal'
        
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_col]
            # Nettoyage des valeurs infinies issues de surfaces à 0
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEUIWN(kBtu/sf)'].fillna(0)

        # 3. Détection IQR 3.0 segmentée par type de propriété
        # Note : On traite ici les distributions (log-normales ou non) avec le même seuil 3.0
        for col in s3_cfg.iqr_vars:
            if col not in df.columns:
                continue 
            
            flag_col = f"is_outlier_iqr_{col}"
            df[flag_col] = 0
            
            # Prétraitement spécifique pour les étages
            temp_df = df.copy()
            if col == "NumberofFloors":
                temp_df = temp_df[temp_df[col] > 0]

            def get_iqr_flags(group):
                clean_group = group.dropna()
                if len(clean_group) < 2:
                    return pd.Series(False, index=group.index)
                
                q1 = clean_group.quantile(0.25)
                q3 = clean_group.quantile(0.75)
                iqr = q3 - q1
                
                if iqr == 0:
                    return pd.Series(False, index=group.index)
                
                # Seul le coefficient 3.0 (outliers extrêmes) est retenu
                lower = q1 - 3.0 * iqr
                upper = q3 + 3.0 * iqr
                return (group < lower) | (group > upper)

            outlier_mask = temp_df.groupby('PrimaryPropertyType')[col].transform(get_iqr_flags)
            df.loc[temp_df.index[outlier_mask == True], flag_col] = 1

        # 4. Décisions stratégiques et validation croisée
        
        # Identification des suspects (Intensités hors-normes)
        mask_suspect_intensity = (df['is_outlier_iqr_SiteEUI(kBtu/sf)'] == 1) | \
                                 (df.get('is_outlier_iqr_GHGEmissionsIntensity', 0) == 1)
        
        # Identification des facteurs justificatifs (Surfaces hors-normes)
        mask_justified_by_size = (df['is_outlier_iqr_PropertyGFATotal'] == 1)
        
        # LOGIQUE SCIENTIFIQUE : 
        # Si (Outlier Intensité) ET NON (Outlier Surface) -> Suppression (Erreur probable)
        # Sinon -> Conservation (Profil atypique mais cohérent physiquement)
        mask_drop = mask_suspect_intensity & (~mask_justified_by_size)
        
        audit["outliers_intensity_removed"] = int(mask_drop.sum())
        audit["outliers_intensity_saved_by_gfa"] = int((mask_suspect_intensity & mask_justified_by_size).sum())
        
        # Application du filtre
        df = df[~mask_drop].copy()

        # 5. Conservation finale des flux et structures
        # On s'assure de ne pas avoir supprimé les flux Gaz/Vapeur/Floors
        audit["massive_surfaces_preserved"] = int((df['is_outlier_iqr_PropertyGFATotal'] == 1).sum())
        audit["high_rise_preserved"] = int((df.get('is_outlier_iqr_NumberofFloors', 0) == 1).sum())
        
        self.audit(df_before, df, audit)
        return df