import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import scipy.stats as stats
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

def evaluate_model(model, X_test, y_test, run_name):
    """
    Évaluation multi-dimensionnelle pour comparaison de modèles.
    """
    y_pred = model.predict(X_test)
    
    # 1. Métriques de performance
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    # MAPE sur les valeurs réelles (inversion du log si nécessaire, ici on reste en log pour la stabilité)
    mape = np.mean(np.abs((y_test - y_pred) / np.abs(y_test))) * 100
    
    metrics = {"R2": r2, "MAE": mae, "RMSE": rmse, "MAPE": mape}

    # 2. Préparation du Dashboard (4 lignes, 2 colonnes)
    fig, axes = plt.subplots(4, 2, figsize=(20, 25))
    fig.suptitle(f"ANALYSE COMPARATIVE : {run_name}\nScore R2 : {r2:.4f}", fontsize=22, fontweight='bold')

    # --- A. Réel vs Prédit log transforme ---
    sns.regplot(x=y_test, y=y_pred, ax=axes[0, 0], scatter_kws={'alpha':0.4}, line_kws={'color':'red'})
    axes[0, 0].set_title("Alignement Prédictif (version log)", fontsize=15)

    # --- B. QQ-Plot log transforme ---
    stats.probplot(y_test - y_pred, dist="norm", plot=axes[0, 1])
    axes[0, 1].set_title("QQ-Plot log transforme : Normalité des erreurs", fontsize=15)

    # --- C. Feature Importance (Absolue) ---
    try:
        raw_model = model.named_steps['model']
        # On gère Ridge (.coef_) et XGB/RF (.feature_importances_)
        if hasattr(raw_model, 'feature_importances_'):
            imps = raw_model.feature_importances_
        else:
            imps = np.abs(raw_model.coef_)
            
        feat_names = model.named_steps['preprocessor'].get_feature_names_out()
        df_imp = pd.Series(imps, index=feat_names).sort_values(ascending=False).head(15)
        sns.barplot(x=df_imp.values, y=df_imp.index, ax=axes[1, 0], palette="flare")
        axes[1, 0].set_title("Top 15 Drivers d'émissions", fontsize=15)
        
        # --- D. Heatmap de Corrélation des Top Features ---
        top_cols = [c.split('__')[-1] for c in df_imp.index[:8]] # Nettoyage noms preprocessor
        existing_cols = [c for c in top_cols if c in X_test.columns]
        if existing_cols:
            corr = X_test[existing_cols].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", ax=axes[1, 1])
            axes[1, 1].set_title("Colinéarité des Top Features", fontsize=15)
    except Exception as e:
        print(f"Info: Importance indisponible ({e})")

    # --- E. Distribution des Résidus ---
    residuals = y_test - y_pred
    sns.histplot(residuals, kde=True, ax=axes[2, 0], color="teal")
    axes[2, 0].axvline(0, color='red', linestyle='--')
    axes[2, 0].set_title("Distribution de l'Erreur", fontsize=15)

    # --- F. Erreur par Type de Propriété ---
    if 'PrimaryPropertyType' in X_test.columns:
        err_df = pd.DataFrame({'Type': X_test['PrimaryPropertyType'], 'Error': np.abs(residuals)})
        order = err_df.groupby('Type')['Error'].mean().sort_values(ascending=False).index
        sns.boxplot(data=err_df, x='Error', y='Type', order=order, ax=axes[2, 1], palette="vlag")
        axes[2, 1].set_title("Variabilité de l'erreur par usage", fontsize=15)

    # --- G. Évolution de l'erreur ---
    axes[3, 0].scatter(y_pred, residuals, alpha=0.4)
    axes[3, 0].axhline(0, color='black', lw=1)
    axes[3, 0].set_xlabel("Valeurs prédites")
    axes[3, 0].set_ylabel("Résidus")
    axes[3, 0].set_title("Hétéroscédasticité", fontsize=15)

    # --- H. Tableau des "Pires Erreurs" ---
    axes[3, 1].axis('off')
    worst_idx = np.argsort(np.abs(residuals))[-5:]
    txt = "TOP 5 - PIRES PRÉDICTIONS :\n\n"
    for idx in worst_idx:
        txt += f"ID: {X_test.index[idx]} | Réel: {y_test.values[idx]:.2f} | Prédit: {y_pred[idx]:.2f}\n"
    axes[3, 1].text(0.1, 0.5, txt, fontsize=12, family='monospace', verticalalignment='center')

    # CORRECTION DU BUG RECT : Utilisation d'un TUPLE
    plt.tight_layout(rect=(0, 0.03, 1, 0.95))
    
    plot_path = f"diagnostic_{run_name}.png"
    plt.savefig(plot_path)
    plt.close()
    
    return metrics, plot_path

def detect_column_types(df):
    """Détecteur robuste."""
    binary_cols = [c for c in df.columns if df[c].nunique() <= 2]
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if c not in binary_cols]
    cat_cols = [c for c in df.columns if c not in num_cols and c not in binary_cols]
    return num_cols, cat_cols, binary_cols