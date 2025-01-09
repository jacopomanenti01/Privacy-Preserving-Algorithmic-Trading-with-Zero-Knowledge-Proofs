import hashlib
import os




def compute_model_hash():
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
        print(model_path)
        with open(model_path, "rb") as f:
            model_data = f.read()
        return hashlib.sha256(model_data).hexdigest()

a = compute_model_hash()
print(a)