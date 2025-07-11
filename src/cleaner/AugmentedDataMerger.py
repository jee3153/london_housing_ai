import base64, requests, pandas as pd
from typing import Dict
import dotenv
from os import environ

dotenv.load_dotenv()

class AugmentedDataMerger:
    def __init__(self):
        self.api_key = environ["EPC_API_KEY"]
        
    