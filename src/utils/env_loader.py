import dotenv
from pathlib import Path
import os
import json

dotenv.load_dotenv()

BASE_PATH = Path(os.getenv("BASE_DIR"))
DATA_FILE = BASE_PATH / "slingshot_storage.json"
OUTPUT_FILE = BASE_PATH / "output.txt"


# Initialize storage if not present
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump({"directories": {}, "commands": [], "saved_commands": []}, f)

if not OUTPUT_FILE.exists():
    with open(OUTPUT_FILE, "w") as f:
        f.write("")

