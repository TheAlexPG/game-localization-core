import os
import re
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ===== НАЛАШТУВАННЯ =====
BATCH_SIZE = 10  # Кількість рядків для перекладу за раз
MAX_PARALLEL_FILES = 5  # Кількість файлів що обробляються паралельно

# OpenAI налаштування
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5"
prompt = "ping"

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a highly precise translation engine. You will receive a list of Russian texts and must return a single, valid JSON object with their Ukrainian translations, preserving all technical tags perfectly."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=1,
                    max_completion_tokens=55000
                )
print(response.choices[0].message.content)