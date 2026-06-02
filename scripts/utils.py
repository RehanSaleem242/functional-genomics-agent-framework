# Utility functions for tokenizer and data processing

import json
from pathlib import Path

def load_tokenizer_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

# Add more helper functions as needed
