import pandas as pd
import numpy as np
from scipy import stats
from .base_processor import BaseCleaner

class Section3(BaseCleaner):
    def run(self, df):
        df = df.copy()
        s3_cfg = self.cfg.cleaning.section_3
        t = s3_cfg.thresholds
        audit = {}

        df["exclusion_reason"] = None

        # ------------------------------------------------------------------
        # 1. Préparation des variables (WN déjà synchronisées en S2)
        # ------------------------------------------------------------------
        surface_col = (
            'PropertyGFABuilding(s)'
            if 'PropertyGFABuilding(s)' in df.columns
            else 'PropertyGFATotal'
        )

        if 'SiteEnergyUseWN(kBtu)' in df.columns and surface_col in df.columns:
            df['SiteEUIWN(kBtu/sf)'] = df['SiteEnergyUseWN(kBtu)'] / df[surface_col]

        # ------------------------------------------------------------------
        # 2. DÉTECTION PAR Z-SCORE (variables normalisées après log)
        # ------------------------------------------------------------------
        zscore_cols = [c for c in s3_cfg.zscore_vars if c in df.columns]

        zscore_stats = {}

        for col in zscore_cols:
            def zscore_log_group(x):
                x_valid = x.dropna()
                if x_valid.count() <= 5:
                    return pd.Series(0, index=x.index)

                # Sécurité : on exclut valeurs négatives avant log
                x_pos = x.clip(lower=0)
                z = stats.zscore(np.log1p(x_pos), nan_policy='omit')
                return z

            df[f'zscore_{col}'] = (
                df.groupby('PrimaryPropertyType')[col]
                  .transform(zscore_log_group)
            )

            # Audit par variable
            z_abs = df[f'zscore_{col}'].abs()
            zscore_stats[col] = {
                "n_obs": int(df[col].notna().sum()),
                "n_extreme_z": int((z_abs > t.zscore_limit).sum()),
                "max_abs_z": float(z_abs.max(skipna=True))
            }

        # ------------------------------------------------------------------
        # 3. DÉTECTION PAR IQR (structure / intensité)
        # ------------------------------------------------------------------
        iqr_cols = [c for c in s3_cfg.iqr_vars if c in df.columns]
        iqr_stats = {}

        for col in iqr_cols:
            def get_iqr_outliers(x):
                if x.count() <= 5:
                    return pd.Series(False, index=x.index)
                q1, q3 = x.quantile(0.25), x.quantile(0.75)
                iqr = q3 - q1
                return (x < (q1 - t.iqr_multiplier * iqr)) | (x > (q3 + t.iqr_multiplier * iqr))

            mask_out = (
                df.groupby('PrimaryPropertyType')[col]
                  .transform(get_iqr_outliers)
            )

            df[f'is_iqr_outlier_{col}'] = mask_out.astype(int)

            iqr_stats[col] = {
                "n_obs": int(df[col].notna().sum()),
                "n_iqr_outliers": int(mask_out.sum())
            }

        # ------------------------------------------------------------------
        # 4. LOGIQUE D’EXCLUSION
        # ------------------------------------------------------------------
        zscore_flag_cols = [f'zscore_{c}' for c in zscore_cols]
        df['extreme_zscore_count'] = (
            df[zscore_flag_cols].abs() > t.zscore_limit
        ).sum(axis=1)

        mask_zscore_limit = df['extreme_zscore_count'] >= t.zscore_sum_limit

        mask_iqr_critical = (
            (df.get('is_iqr_outlier_SiteEUI(kBtu/sf)', 0) == 1) |
            (df.get('is_iqr_outlier_PropertyGFATotal', 0) == 1)
        )

        mask_massive = df['PrimaryPropertyType'].isin(
            s3_cfg.massive_structures_types
        )

        mask_drop = (mask_zscore_limit | mask_iqr_critical) & (~mask_massive)

        # Raisons d’exclusion
        df.loc[mask_zscore_limit, "exclusion_reason"] = (
            f"ZScoreSum≥{t.zscore_sum_limit}"
        )
        df.loc[
            mask_iqr_critical & df["exclusion_reason"].isna(),
            "exclusion_reason"
        ] = "Critical IQR Outlier"

        # ------------------------------------------------------------------
        # 5. NETTOYAGE FINAL
        # ------------------------------------------------------------------
        df_after = df[~mask_drop].copy()

        cols_to_drop = [
            c for c in df.columns
            if (c.startswith('zscore_') or c.startswith('is_iqr_'))
            and c != 'extreme_zscore_count'
        ]

        df_final = df_after.drop(
            columns=cols_to_drop + ["exclusion_reason"],
            errors='ignore'
        )

        # ------------------------------------------------------------------
        # 6. AUDIT ENRICHI
        # ------------------------------------------------------------------
        audit.update({
            "zscore": zscore_stats,
            "iqr": iqr_stats,
            "rows_flagged_zscore_sum": int(mask_zscore_limit.sum()),
            "rows_flagged_iqr_critical": int(mask_iqr_critical.sum()),
            "massive_structures_preserved": int(
                (mask_massive & (mask_zscore_limit | mask_iqr_critical)).sum()
            ),
            "total_section3_removed": int(mask_drop.sum()),
            "share_removed": float(mask_drop.mean())
        })

        self.audit(df, df_final, audit)
        return df_final