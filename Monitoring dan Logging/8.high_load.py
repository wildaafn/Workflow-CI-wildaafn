import time
import requests
import random

url = "http://localhost:8000/predict"
print("Generating high load to trigger HighRequestRate alert...")
start_time = time.time()
count = 0

# Run for 90 seconds to ensure the 1-minute alert triggers and fires
while time.time() - start_time < 90:
    try:
        response = requests.post(url)
        count += 1
        if count % 100 == 0:
            print(f"Sent {count} requests... Last status: {response.status_code}")
    except Exception as e:
        print(f"Error sending request: {e}")
    # Sleep slightly to maintain a high request rate (approx 20 requests/sec)
    time.sleep(0.04)

print(f"Load generation finished. Total requests sent: {count}")
