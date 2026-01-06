import numpy as np
import logging
from .base_processor import BaseCleaner

logger = logging.getLogger(__name__)

class Section2(BaseCleaner):
    def run(self, df):
        # On travaille sur une copie pour le marquage
        df = df.copy()
        conf = self.cfg.cleaning.section_2
        c = conf.columns
        t = conf.thresholds
        v = conf["values"] 
        
        # Initialisation de la colonne de diagnostic
        df["exclusion_reason"] = None

        # --- 0. SYNCHRONISATION DES VARIABLES WN (PRIORITÉ PHYSIQUE) ---
        # Si une variable normalisée (WN) est nulle/NaN alors que la brute est > 0,
        # on restaure la valeur brute pour assurer la cohérence des audits suivants.
        
        # Liste des paires (Brute, WN) à synchroniser
        wn_sync_map = {
            c.energy_total: 'SiteEnergyUseWN(kBtu)',
            'SiteEUI(kBtu/sf)': 'SiteEUIWN(kBtu/sf)',
            'SourceEUI(kBtu/sf)': 'SourceEUIWN(kBtu/sf)'
        }

        for raw_col, wn_col in wn_sync_map.items():
            if raw_col in df.columns and wn_col in df.columns:
                mask_fix = (df[raw_col] > 0) & (df[wn_col].isna() | (df[wn_col] == 0))
                df.loc[mask_fix, wn_col] = df.loc[mask_fix, raw_col]

        # 1. Filtre GFA (Surfaces)
        mask_gfa_invalid = df[c.gfa_total] <= t.min_gfa
        df.loc[mask_gfa_invalid, "exclusion_reason"] = f"Invalid GFA (<= {t.min_gfa})"

        # 2. Filtre Énergies (Valeurs négatives)
        energy_vars = [c.energy_total, c.ghg_emissions, c.electricity, c.natural_gas]
        mask_energy_invalid = (df[energy_vars] < t.min_energy).any(axis=1)
        df.loc[mask_energy_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Negative Energy/GHG values"

        # 3. Diagnostic des Étages (SANS IMPUTATION)
        df['IsZeroFloorReported'] = (df[c.floors] <= 0).astype(int)
        df['IsAggregatedCampus'] = (df[c.building_type] == v.campus_label).astype(int)
        
        mask_bad_floors = (df[c.floors] <= 0)
        df.loc[mask_bad_floors, c.floors] = np.nan

        # 4. Recalcul des intensités (EUI)
        # Maintenant basé sur des données WN synchronisées
        surface_ref = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else c.gfa_total
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_ref]
            # Sécurité contre les divisions par zéro/infinis
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # 5. Ratios de cohérence GFA
        df['gfa_ratio'] = df[c.largest_use_gfa] / df[c.gfa_total]
        mask_gfa_ratio_invalid = (df['gfa_ratio'] > t.ratio_critical)
        df.loc[mask_gfa_ratio_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Incoherent GFA Ratio"

        # 6. Vérification de la somme des sources d'énergie
        energy_cols = [c.electricity, c.natural_gas]
        if hasattr(c, 'steam') and c.steam in df.columns:
            energy_cols.append(c.steam)
            
        sum_sources = df[energy_cols].sum(axis=1, min_count=1)
        
        # Utilisation de la variable WN synchronisée pour la comparaison
        target_energy = 'SiteEnergyUseWN(kBtu)' if 'SiteEnergyUseWN(kBtu)' in df.columns else c.energy_total
        
        rel_diff = (sum_sources - df[target_energy]).abs() / df[target_energy].replace(0, np.nan)
        
        mask_energy_sum_invalid = (rel_diff > t.energy_sum_error_max)
        df.loc[mask_energy_sum_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Energy Sum Mismatch"

        # --- PREPARATION DE LA SORTIE ---
        df_after = df[df["exclusion_reason"].isna()].copy()
        
        cols_to_drop = ["exclusion_reason", "gfa_ratio"]
        df_after = df_after.drop(columns=cols_to_drop, errors='ignore')

        # 7. Audit détaillé
        audit_details = {
            "rows_removed_invalid_gfa": int(mask_gfa_invalid.sum()),
            "rows_removed_invalid_energy_vals": int(mask_energy_invalid.sum()),
            "potential_floors_to_impute": int(mask_bad_floors.sum()),
            "rows_removed_gfa_ratio_incoherent": int(mask_gfa_ratio_invalid.sum()),
            "rows_removed_energy_sum_incoherent": int(mask_energy_sum_invalid.sum())
        }

        self.audit(df, df_after, audit_details)
        
        return df_after