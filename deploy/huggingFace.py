from huggingface_hub import HfApi
from dotenv import load_dotenv
import os


load_dotenv
api=HfApi(token=os.getenv("HF_TOKEN"))

try:
    api.upload_file(
        path_or_fileobj="../model/randomforest_tuned_model.pkl",
        path_in_repo="randomforest_tuned_model.pkl", 
        repo_id="Sidikat123/Centralised-Data-Platform-Model", 
        repo_type="model",
    )
except Exception as e:
    print(f"Upload failed: {str(e)}")