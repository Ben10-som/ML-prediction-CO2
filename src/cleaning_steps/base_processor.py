import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from omegaconf import OmegaConf

class BaseCleaner:
    def __init__(self, name, cfg):
        self.name = name
        self.cfg = cfg
        self.metadata = {}
        self.df_removed = pd.DataFrame() # <-- Stockage temporaire des lignes supprimées

    def audit(self, df_before, df_after, details=None):
        # 1. Identifier les lignes supprimées par comparaison d'index
        removed_indices = df_before.index.difference(df_after.index)
        self.df_removed = df_before.loc[removed_indices].copy()

        # 2. Mise à jour de la metadata
        self.metadata = {
            "step": self.name,
            "timestamp": datetime.now().isoformat(),
            "rows_before": int(len(df_before)),
            "rows_after": int(len(df_after)),
            "rows_removed": int(len(self.df_removed)),
            "cols_before": int(df_before.shape[1]),
            "cols_after": int(df_after.shape[1]),
            "details": details or {}
        }

    def save_step(self, df, interim_path):
        step_file = interim_path / f"{self.name}.csv"
        removed_file = interim_path / f"{self.name}_removed.csv" # <-- Nouveau fichier
        meta_file = interim_path / f"{self.name}_metadata.json"
        
        # Sauvegarde du flux principal
        df.to_csv(step_file, index=False)
        
        # Sauvegarde des lignes supprimées (si il y en a)
        if not self.df_removed.empty:
            self.df_removed.to_csv(removed_file, index=True) # On garde l'index pour traçabilité
        
        # Résolution des métadonnées
        try:
            temp_conf = OmegaConf.create(self.metadata)
            serializable_meta = OmegaConf.to_container(temp_conf, resolve=True)
        except Exception:
            # Si ça échoue (ex: self.metadata n'est pas un dict), on garde tel quel
            serializable_meta = self.metadata

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(serializable_meta, f, indent=4, ensure_ascii=False)
            
        print(f"   [Audit] {self.name} : -{self.metadata['rows_removed']} lignes exportées vers {removed_file.name}")  
        return df