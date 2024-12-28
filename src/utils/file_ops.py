import json
import os
from pathlib import Path

from utils.env_loader import DATA_FILE, OUTPUT_FILE



def load_directories():
    """Load saved directories from storage."""
    with open(DATA_FILE, "r") as f:
        return json.load(f)["directories"]


def save_directory(directory):
    """Save directories to storage."""
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}  # Handle empty or invalid JSON
    else:
        data = {}

    data["directories"][directory] = directory

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_terminal_commands():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        return data["commands"]


def save_terminal_commands(command):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    with open(DATA_FILE, "w") as f:
        if isinstance(command, list):
            data["commands"] = command
        else:
            data["commands"].append(command)
        json.dump(data, f)

def load_saved_commands():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        return data["saved_commands"]
    

def save_saved_commands(command):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    
    data["saved_commands"].append(command)
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def add_current_directory():
    """Add the current directory to the list of saved directories."""
    current_dir = os.getcwd()
    save_directory(current_dir)
