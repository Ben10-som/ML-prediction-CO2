#
#
# Lors de la modélisation cette section ne sera appliqué qu'aprés le split train/test
#
"""
Module de nettoyage et d'imputation des données (Section 1).

Ce script gère l'étape de filtrage final de conformité, l'ingénierie de caractéristiques 
initiale et l'imputation en cascade des valeurs manquantes pour le dataset 
Seattle Energy Benchmarking 2016.

Processus :
1. Filtrage des non-conformités et des outliers pré-identifiés.
2. Création de flags (MixedUse, Has_EnergyStar).
3. Imputation groupée par usage primaire (médiane) puis globale.
4. Suppression des lignes avec un taux de données manquantes critique.
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, Any
from .base_processor import BaseCleaner

class Section1(BaseCleaner):
    """
    Processeur de nettoyage pour la Section 1 : Imputation et Conformité.
    
    Attributes:
        cfg: Configuration globale injectée via le pipeline.
    """

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Exécute le pipeline de la section 1.
        
        Args:
            df: DataFrame issu de la section précédente.
            
        Returns:
            pd.DataFrame: Données nettoyées et imputées.
        """
        df = df.copy()
        s1_cfg = self.cfg.cleaning.section_1
        s2_cols = self.cfg.cleaning.section_2.columns
        enable_imputation = s1_cfg.get("enable_imputation", True)
        audit_details = {
            "initial_count": len(df),
            "rejections": {},
            "imputation_enabled": enable_imputation
        }

        # --- 1. SÉCURITÉ ET FILTRAGE DE CONFORMITÉ ---
        if "exclusion_reason" not in df.columns:
            df["exclusion_reason"] = None

        # Identification des outliers marqués par la ville
        if 'Outlier' in df.columns:
            mask_outlier = df['Outlier'].notna() & (df['Outlier'].astype(str).str.strip() != "")
            df.loc[mask_outlier, "exclusion_reason"] = "Pre-marked Outlier"
            audit_details["rejections"]["pre_marked_outliers"] = int(mask_outlier.sum())

        # Filtrage de conformité administrative
        if 'ComplianceStatus' in df.columns:
            mask_non_compliant = df['ComplianceStatus'] != s1_cfg.compliance_value
            df.loc[mask_non_compliant & df["exclusion_reason"].isna(), "exclusion_reason"] = "Non-Compliant Status"
            audit_details["rejections"]["non_compliant"] = int(mask_non_compliant.sum())

        # Application du filtre initial
        mask_to_remove = df["exclusion_reason"].notna()
        df_working = df[~mask_to_remove].copy()

        # --- 2. FEATURE ENGINEERING ---
        # Identification des usages mixtes
        df_working['IsMixedUse'] = df_working['SecondLargestPropertyUseType'].notna().astype(int)
        
        # Flag de présence EnergyStar (utile pour les modèles prédictifs)
        if 'ENERGYSTARScore' in df_working.columns:
            df_working['Has_EnergyStarScore'] = df_working['ENERGYSTARScore'].notna().astype(int)
        

        # --- 2.5 REPARATION DES CATEGORIES CRITIQUES ---
        # Cela ne concerne que 4 batiments,comme meilleur strategie on examinera ces 4 elements
        # Si le type d'usage principal est vide, on utilise le type de propriété primaire
        if 'LargestPropertyUseType' in df_working.columns:
            mask_missing_type = df_working['LargestPropertyUseType'].isnull()
            df_working.loc[mask_missing_type, 'LargestPropertyUseType'] = df_working.loc[mask_missing_type, 'PrimaryPropertyType']
            
            # Si c'est toujours vide (cas rare), on met "Unknown" pour permettre le groupby
            df_working['LargestPropertyUseType'] = df_working['LargestPropertyUseType'].fillna("Unknown")


        # --- 3. IMPUTATIONS EN CASCADE (Usage -> Global) ---
        # A appliquer uniquement si if enable_imputation=True

        # Calcul du taux de NA avant imputation pour l'audit
        if enable_imputation:
            missing_before = df_working.isnull().sum()
            usage_col = s2_cols.primary_usage
            
            # Sélection des colonnes numériques ayant des valeurs manquantes
            cols_to_impute = df_working.select_dtypes(include=[np.number]).columns
            cols_to_impute = [c for c in cols_to_impute if df_working[c].isnull().any()]

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Mean of empty slice")
                for col in cols_to_impute:
                    # Étape A : Médiane par type d'usage (plus précis)
                    df_working[col] = df_working.groupby(usage_col)[col].transform(
                        lambda x: x.fillna(x.median())
                    )
                    # Étape B : Médiane globale (si le groupe d'usage était entièrement vide)
                    df_working[col] = df_working[col].fillna(df_working[col].median())

                    # Post-traitement spécifique (ex: les étages doivent être entiers)
                    if col == s2_cols.floors:
                        df_working[col] = df_working[col].round().astype(int)

            audit_details["imputed_columns"] = {col: int(missing_before[col]) for col in cols_to_impute}
        else:
            audit_details["imputed_columns"] = {}

        # --- 4. SUPPRESSION DES LIGNES TROP VIDES ---
        row_missing_pct = df_working.isnull().mean(axis=1)
        mask_too_many_missing = row_missing_pct > s1_cfg.thresholds.row_max_missing_pct
        
        rejected_indices = df_working.index[mask_too_many_missing]
        df.loc[rejected_indices, "exclusion_reason"] = "Excessive Missing Data"
        audit_details["rejections"]["excessive_missing"] = int(mask_too_many_missing.sum())

        df_final = df_working[~mask_too_many_missing].copy()

        # --- 5. NETTOYAGE FINAL DES COLONNES ---
        cols_to_drop = [c for c in s1_cfg.cols_to_drop if c in df_final.columns]
        df_final.drop(columns=cols_to_drop, inplace=True)
        audit_details["dropped_columns"] = cols_to_drop

        # --- 6. AUDIT ET RETOUR ---
        self.audit(df, df_final, audit_details)
        
        return df_final