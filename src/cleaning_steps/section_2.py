import numpy as np
import logging
from .base_processor import BaseCleaner

logger = logging.getLogger(__name__)

class Section2(BaseCleaner):
    """
    Nettoyage et synchronisation des données énergétiques et surfaces.
    """
    def run(self, df):
        df = df.copy()
        
        # Accès sécurisé à la configuration
        conf = self.cfg.cleaning.section_2
        c = conf.columns
        t = conf.thresholds
        
        # CORRECTION AttributeError : On force l'accès par dictionnaire
        # car .values est une méthode réservée en Python/OmegaConf
        v = conf["values"] 
        
        # CORRECTION FutureWarning : Initialisation en type 'object' (string)
        # pour éviter le conflit avec les flottants
        df["exclusion_reason"] = df["exclusion_reason"] = np.nan
        df["exclusion_reason"] = df["exclusion_reason"].astype(object)

        # --- SYNCHRONISATION DES VARIABLES WN ---
        wn_sync_map = {
            c.energy_total: 'SiteEnergyUseWN(kBtu)',
            'SiteEUI(kBtu/sf)': 'SiteEUIWN(kBtu/sf)',
            'SourceEUI(kBtu/sf)': 'SourceEUIWN(kBtu/sf)'
        }

        for raw_col, wn_col in wn_sync_map.items():
            if raw_col in df.columns and wn_col in df.columns:
                missing_wn = (df[raw_col] > 0) & (df[wn_col].isna() | (df[wn_col] == 0))
                aberrant_wn = (df[raw_col] > 100) & (df[wn_col] < (df[raw_col] * 0.1))
                
                mask_fix = missing_wn | aberrant_wn
                if mask_fix.sum() > 0:
                    df.loc[mask_fix, wn_col] = df.loc[mask_fix, raw_col]

        # 1. Filtre GFA
        mask_gfa_invalid = df[c.gfa_total] <= t.min_gfa
        df.loc[mask_gfa_invalid, "exclusion_reason"] = f"Invalid GFA (<= {t.min_gfa})"

        # 2. Filtre Énergies
        energy_vars = [c.energy_total, c.ghg_emissions, c.electricity, c.natural_gas]
        existing_vars = [col for col in energy_vars if col in df.columns]
        mask_energy_invalid = (df[existing_vars] < t.min_energy).any(axis=1)
        df.loc[mask_energy_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Negative Energy/GHG values"

        # 3. Diagnostic des Étages
        df['IsZeroFloorReported'] = (df[c.floors] <= 0).astype(int)
        # Utilisation de v.campus_label après correction de l'accès à 'values'
        df['IsAggregatedCampus'] = (df[c.building_type] == v.campus_label).astype(int)
        mask_bad_floors = (df[c.floors] <= 0)
        df.loc[mask_bad_floors, c.floors] = np.nan

        # 4. Recalcul EUI
        surface_ref = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else c.gfa_total
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_ref].replace(0, np.nan)
            df.replace([np.inf, -np.inf], np.nan, inplace=True)

        # 5. Ratios GFA
        df['gfa_ratio'] = df[c.largest_use_gfa] / df[c.gfa_total].replace(0, np.nan)
        mask_gfa_ratio_invalid = (df['gfa_ratio'] > t.ratio_critical)
        df.loc[mask_gfa_ratio_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Incoherent GFA Ratio"

        # 6. Somme des sources
        energy_cols = [c.electricity, c.natural_gas]
        if hasattr(c, 'steam') and c.steam in df.columns:
            energy_cols.append(c.steam)
            
        sum_sources = df[energy_cols].sum(axis=1, min_count=1)
        target_energy_check = c.energy_total 
        
        rel_diff = (sum_sources - df[target_energy_check]).abs() / df[target_energy_check].replace(0, np.nan)
        mask_energy_sum_invalid = (rel_diff > t.energy_sum_error_max)
        df.loc[mask_energy_sum_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Energy Sum Mismatch"

        # --- PRÉPARATION SORTIE ---
        df_after = df[df["exclusion_reason"].isna()].copy()
        cols_to_drop = ["exclusion_reason", "gfa_ratio"]
        df_after = df_after.drop(columns=cols_to_drop, errors='ignore')

        audit_details = {
            "rows_removed_invalid_gfa": int(mask_gfa_invalid.sum()),
            "rows_removed_invalid_energy_vals": int(mask_energy_invalid.sum()),
            "potential_floors_to_impute": int(mask_bad_floors.sum()),
            "rows_removed_gfa_ratio_incoherent": int(mask_gfa_ratio_invalid.sum()),
            "rows_removed_energy_sum_incoherent": int(mask_energy_sum_invalid.sum())
        }

        self.audit(df, df_after, audit_details)
        
        return df_after
        