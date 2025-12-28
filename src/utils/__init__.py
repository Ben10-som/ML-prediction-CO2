"""
Utilitaires généraux du projet
Ce package regroupe des fonctions d'aide réutilisables
pour la configuration et la gestion des chemins.
"""

from .config_loader import load_config, get_paths
# Cela permet de les rendre accessibles directement via src.utils

__all__ = ['load_config', 'get_paths']
# Définition de l'API publique du package utils
# Seules ces fonctions seront exposées lors d'un import global