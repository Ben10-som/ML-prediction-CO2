import pandas as pd
import numpy as np
import logging
from .base_processor import BaseCleaner

logger = logging.getLogger(__name__)

class Section2(BaseCleaner):
    def run(self, df):
        df_before = df.copy()
        conf = self.cfg.cleaning.section_2
        c = conf.columns
        t = conf.thresholds
        v = conf["values"] 
        
        # 1. Filtre GFA (Surfaces)
        mask_gfa_invalid = df[c.gfa_total] <= t.min_gfa
        df = df[~mask_gfa_invalid].copy()

        # 2. Filtre Énergies
        energy_vars = [c.energy_total, c.ghg_emissions, c.electricity, c.natural_gas]
        mask_energy_invalid = (df[energy_vars] < t.min_energy).any(axis=1)
        df = df[~mask_energy_invalid].copy()

        # 3. Traitement des Étages (Imputation systématique pour TOUS les <= 0)
        # On définit les flags AVANT pour pouvoir les utiliser dans l'audit
        df['IsZeroFloorReported'] = (df[c.floors] <= 0).astype(int)
        df['IsAggregatedCampus'] = (df[c.building_type] == v.campus_label).astype(int)
        
        # DEFINITION DU MASQUE (C'est ce qui manquait dans ton erreur)
        mask_impute_floors = (df[c.floors] <= 0)
        
        # Passage en NaN pour l'imputation
        df.loc[mask_impute_floors, c.floors] = np.nan
        
        # Imputation par la médiane du groupe (PrimaryPropertyType)
        df[c.floors] = df.groupby(c.primary_usage)[c.floors].transform(lambda x: x.fillna(x.median()))
        
        # Fallback global et finalisation
        df[c.floors] = df[c.floors].fillna(df[c.floors].median()).round().astype(int)

        # 4. Recalcul des intensités (EUI) - ALIGNÉ SEATTLE (Building GFA)
        surface_ref = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else c.gfa_total
        
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_ref]
            
            if 'SourceEnergyUseWN(kBtu)' in df.columns:
                df['SourceEUIWN(kBtu/sf)'] = df['SourceEnergyUseWN(kBtu)'] / df[surface_ref]
        
        df.replace([np.inf, -np.inf], 0, inplace=True)

        # 5. Ratios de cohérence GFA
        df['gfa_ratio'] = df[c.largest_use_gfa] / df[c.gfa_total]
        mask_gfa_ratio_invalid = df['gfa_ratio'] > t.ratio_critical
        df = df[~mask_gfa_ratio_invalid].copy()

        # 6. Vérification de la somme des sources d'énergie
        energy_cols = [c.electricity, c.natural_gas]
        if hasattr(c, 'steam') and c.steam in df.columns:
            energy_cols.append(c.steam)
            
        sum_sources = df[energy_cols].sum(axis=1)
        rel_diff = (sum_sources - df[c.energy_total]).abs() / df[c.energy_total]
        mask_energy_sum_invalid = rel_diff > t.energy_sum_error_max
        df = df[~mask_energy_sum_invalid].copy()

        # 7. Audit détaillé (CORRIGÉ)
        audit_details = {
            "rows_removed_invalid_gfa": int(mask_gfa_invalid.sum()),
            "rows_removed_invalid_energy_vals": int(mask_energy_invalid.sum()),
            "total_floors_imputed": int(mask_impute_floors.sum()),
            # On compte les lignes imputées qui étaient aussi des Campus
            "campus_floors_imputed": int((mask_impute_floors & (df['IsAggregatedCampus'] == 1)).sum()),
            "rows_removed_gfa_ratio_incoherent": int(mask_gfa_ratio_invalid.sum()),
            "rows_removed_energy_sum_incoherent": int(mask_energy_sum_invalid.sum())
        }

        self.audit(df_before, df, audit_details)
        return df