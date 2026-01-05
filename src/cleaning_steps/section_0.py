from .base_processor import BaseCleaner

class Section0(BaseCleaner):
    def run(self, df):
        df_before = df.copy()
        
        # Harmonisation des libellés
        df["BuildingType"] = df["BuildingType"].replace({
            "Nonresidential WA": "NonResidential"
        })
        
        #  exclusion par BuildingType et PrimaryPropertyType
        building_types_to_exclude = self.cfg.cleaning.section_0.exclude_building_types
        primary_types_to_exclude = self.cfg.cleaning.section_0.exclude_primary_property_types
        
        mask = (
            ~df['BuildingType'].isin(building_types_to_exclude)
            & ~df['PrimaryPropertyType'].isin(primary_types_to_exclude)
        )
        df_after = df[mask].copy()
        
        # Audit
        self.audit(df_before, df_after, {
            "excluded_building_types": building_types_to_exclude,
            "excluded_primary_property_types": primary_types_to_exclude,
            "replacements": {"Nonresidential WA": "NonResidential"},
            "action": "Restriction aux populations non-résidentielles + harmonisation des libellés"
        })
        
        return df_after
