import sys
import os
from pathlib import Path

# Add dashboard/backend to path to import api
backend_path = Path("dashboard/backend").resolve()
sys.path.append(str(backend_path))

try:
    from api import retrain
    print("Trigging model retraining...")
    result = retrain()
    print(f"Retrain result: {result}")
except Exception as e:
    print(f"Error during retraining: {e}")
    sys.exit(1)
