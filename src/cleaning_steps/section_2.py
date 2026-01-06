import numpy as np
import logging
from .base_processor import BaseCleaner

logger = logging.getLogger(__name__)

class Section2(BaseCleaner):
    def run(self, df):
        # On travaille sur une copie pour le marquage
        df = df.copy()
        df_before = df.copy()
        conf = self.cfg.cleaning.section_2
        c = conf.columns
        t = conf.thresholds
        v = conf["values"] 
        
        # Initialisation de la colonne de diagnostic
        df["exclusion_reason"] = None

        # 1. Filtre GFA (Surfaces)
        mask_gfa_invalid = df[c.gfa_total] <= t.min_gfa
        df.loc[mask_gfa_invalid, "exclusion_reason"] = f"Invalid GFA (<= {t.min_gfa})"

        # 2. Filtre Énergies (Valeurs négatives ou aberrantes)
        energy_vars = [c.energy_total, c.ghg_emissions, c.electricity, c.natural_gas]
        # On ne marque que ceux qui n'ont pas déjà été exclus par la GFA
        mask_energy_invalid = (df[energy_vars] < t.min_energy).any(axis=1)
        df.loc[mask_energy_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Negative Energy/GHG values"

        # 3. Traitement des Étages (Flags de diagnostic)
        df['IsZeroFloorReported'] = (df[c.floors] <= 0).astype(int)
        df['IsAggregatedCampus'] = (df[c.building_type] == v.campus_label).astype(int)
        mask_impute_floors = (df[c.floors] <= 0)
        
        # Imputation (uniquement sur les survivants potentiels pour la performance)
        df.loc[mask_impute_floors, c.floors] = np.nan
        df[c.floors] = df.groupby(c.primary_usage)[c.floors].transform(lambda x: x.fillna(x.median()))
        df[c.floors] = df[c.floors].fillna(df[c.floors].median()).round().astype(int)

        # 4. Recalcul des intensités (EUI)
        surface_ref = 'PropertyGFABuilding(s)' if 'PropertyGFABuilding(s)' in df.columns else c.gfa_total
        if 'SiteEnergyUseWN(kBtu)' in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_ref]
        
        # 5. Ratios de cohérence GFA
        df['gfa_ratio'] = df[c.largest_use_gfa] / df[c.gfa_total]
        mask_gfa_ratio_invalid = df['gfa_ratio'] > t.ratio_critical
        df.loc[mask_gfa_ratio_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Incoherent GFA Ratio"

        # 6. Vérification de la somme des sources d'énergie
        energy_cols = [c.electricity, c.natural_gas]
        if hasattr(c, 'steam') and c.steam in df.columns:
            energy_cols.append(c.steam)
            
        sum_sources = df[energy_cols].sum(axis=1)
        # Calcul de la différence relative
        rel_diff = (sum_sources - df[c.energy_total]).abs() / df[c.energy_total].replace(0, np.nan)
        mask_energy_sum_invalid = rel_diff > t.energy_sum_error_max
        df.loc[mask_energy_sum_invalid & df["exclusion_reason"].isna(), "exclusion_reason"] = "Energy Sum Mismatch"

        # --- PREPARATION DE LA SORTIE ---
        # On définit df_after (ceux qui n'ont AUCUNE raison d'exclusion)
        df_after = df[df["exclusion_reason"].isna()].copy()
        
        # Nettoyage des colonnes techniques pour le flux suivant
        cols_to_drop = ["exclusion_reason", "gfa_ratio"]
        df_after = df_after.drop(columns=cols_to_drop, errors='ignore')

        # 7. Audit détaillé
        audit_details = {
            "rows_removed_invalid_gfa": int(mask_gfa_invalid.sum()),
            "rows_removed_invalid_energy_vals": int(mask_energy_invalid.sum()),
            "total_floors_imputed": int(mask_impute_floors.sum()),
            # On compte les lignes imputées qui étaient aussi des Campus
            "campus_floors_imputed": int((mask_impute_floors & (df['IsAggregatedCampus'] == 1)).sum()),
            "rows_removed_gfa_ratio_incoherent": int(mask_gfa_ratio_invalid.sum()),
            "rows_removed_energy_sum_incoherent": int(mask_energy_sum_invalid.sum())
        }

        # On envoie 'df' à l'audit pour que le CSV Removed contienne 'exclusion_reason'
        self.audit(df, df_after, audit_details)
        
        return df_after