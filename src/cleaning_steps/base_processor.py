import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from omegaconf import OmegaConf

class BaseCleaner:
    def __init__(self, name, cfg):
        self.name = name # <-- On garde 'name'
        self.cfg = cfg
        self.metadata = {}

    def audit(self, df_before, df_after, details=None):
        self.metadata = {
            "step": self.name,
            "timestamp": datetime.now().isoformat(),
            "rows_before": int(len(df_before)),
            "rows_after": int(len(df_after)),
            "rows_removed": int(len(df_before) - len(df_after)),
            "cols_before": int(df_before.shape[1]),
            "cols_after": int(df_after.shape[1]),
            "details": details or {}
        }


    def save_step(self, df, interim_path):
        step_file = interim_path / f"{self.name}.csv"
        meta_file = interim_path / f"{self.name}_metadata.json"
        
        df.to_csv(step_file, index=False)
        
        # On convertit le dictionnaire en objet OmegaConf temporairement 
        # pour bénéficier de la résolution récursive des variables (${...})
        # PUIS on le transforme en container standard.
        try:
            temp_conf = OmegaConf.create(self.metadata)
            serializable_meta = OmegaConf.to_container(temp_conf, resolve=True)
        except Exception:
            # Si ça échoue (ex: self.metadata n'est pas un dict), on garde tel quel
            serializable_meta = self.metadata

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(serializable_meta, f, indent=4, ensure_ascii=False)
            
        print(f"   [Audit] {self.name} : -{self.metadata['rows_removed']} lignes | {self.metadata['rows_after']} restantes.")  
        return df  
