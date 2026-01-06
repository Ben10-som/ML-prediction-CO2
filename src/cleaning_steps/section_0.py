from .base_processor import BaseCleaner

class Section0(BaseCleaner):
    def run(self, df):
        # On travaille sur une copie pour marquer les raisons sans polluer le flux principal
        df = df.copy()
        df_before = df.copy()
        
        # 1. Harmonisation des libellés (Prétraitement)
        df["BuildingType"] = df["BuildingType"].replace({
            "Nonresidential WA": "NonResidential"
        })
        
        # 2. Définition des critères d'exclusion depuis la config
        building_types_to_exclude = self.cfg.cleaning.section_0.exclude_building_types
        primary_types_to_exclude = self.cfg.cleaning.section_0.exclude_primary_property_types

        # 3. Marquage des raisons (C'est ici que le CSV Removed devient informatif)
        # On crée une colonne temporaire pour expliquer pourquoi on supprime
        df["exclusion_reason"] = None
        
        mask_bld = df['BuildingType'].isin(building_types_to_exclude)
        mask_pri = df['PrimaryPropertyType'].isin(primary_types_to_exclude)
        
        df.loc[mask_bld, "exclusion_reason"] = "BuildingType Excluded"
        df.loc[mask_pri, "exclusion_reason"] = "PrimaryPropertyType Excluded"
        # Cas où les deux critères sont rencontrés
        df.loc[mask_bld & mask_pri, "exclusion_reason"] = "Both Types Excluded"

        # 4. Application du filtre
        # On ne garde que ceux qui n'ont pas de raison d'exclusion
        df_after = df[df["exclusion_reason"].isna()].copy()
        
        # On supprime la colonne de diagnostic du flux de sortie final 
        # pour que df_after reste propre pour la Section 1
        df_after = df_after.drop(columns=["exclusion_reason"])

        # 5. Audit détaillé
        # Ici, on passe 'df' (qui contient encore les 100% de lignes + les raisons) 
        # comme df_before à l'audit pour que le CSV Removed capture la colonne 'exclusion_reason'
        self.audit(df, df_after, {
            "excluded_building_types": building_types_to_exclude,
            "excluded_primary_property_types": primary_types_to_exclude,
            "counts": {
                "by_building_type": int(mask_bld.sum()),
                "by_primary_type": int(mask_pri.sum())
            },
            "action": "Nettoyage initial : filtrage par types et harmonisation"
        })
        
        return df_after