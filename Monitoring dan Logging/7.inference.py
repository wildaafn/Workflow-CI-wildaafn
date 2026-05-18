import requests
import time
import random

url = "http://localhost:8000/predict"

print("Starting to send inference requests to the model...")
try:
    for i in range(100):
        response = requests.post(url)
        print(f"Request {i+1}: Status Code {response.status_code}, Response: {response.json()}")
        time.sleep(random.uniform(0.5, 2.0))
except KeyboardInterrupt:
    print("Inference simulation stopped.")
