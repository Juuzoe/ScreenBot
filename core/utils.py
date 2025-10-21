import time
import os
import logging
import hashlib
from PIL import Image
import numpy as np

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def ensure_dir(path: str):
    if path and not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def now_ts():
    return time.strftime("%Y%m%d-%H%M%S")

def image_hash(arr: np.ndarray) -> str:
    img = Image.fromarray(arr[:, :, ::-1])  # BGR→RGB
    img = img.resize((64, 36))
    return hashlib.sha1(img.tobytes()).hexdigest()[:12]
