import time
import psutil
import pickle
import pandas as pd
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import uvicorn

app = FastAPI()

# Add prometheus asgi middleware to route /metrics requests
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Load model and dataset for real inference
MODEL_PATH = "SMSML_wildaafn/Membangun_model/mlruns/0/1fec653a82c94a4984bf3db69cc5847c/artifacts/model/model.pkl"
DATA_PATH = "SMSML_wildaafn/Membangun_model/breast_cancer_preprocessing.csv"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

df = pd.read_csv(DATA_PATH)
target_col = df.columns[-1]
X = df.drop(target_col, axis=1)

class PredictionRequest(BaseModel):
    feature_569: Optional[float] = None
    feature_30: Optional[float] = None
    feature_malignant: Optional[float] = None

# Define Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'App Request Count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['endpoint'])
SYSTEM_MEMORY = Gauge('system_memory_usage_bytes', 'System memory usage in bytes')
SYSTEM_CPU = Gauge('system_cpu_usage_percent', 'System CPU usage percent')
MODEL_PREDICTION = Counter('model_prediction_count', 'Count of model predictions', ['prediction_class'])

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(process_time)
    
    # Update system metrics
    SYSTEM_MEMORY.set(psutil.virtual_memory().used)
    SYSTEM_CPU.set(psutil.cpu_percent())
    
    return response

@app.post("/predict")
async def predict(data: Optional[PredictionRequest] = None):
    # Determine the input features to use for inference
    if data and data.feature_569 is not None and data.feature_30 is not None and data.feature_malignant is not None:
        input_df = pd.DataFrame([{
            '569': data.feature_569,
            '30': data.feature_30,
            'malignant': data.feature_malignant
        }])
    else:
        # Sample a random row from the actual dataset for real inference
        input_df = X.sample(1)
    
    # Perform actual inference using the loaded model
    prediction = int(model.predict(input_df)[0])
    
    # Increment the Prometheus metric using the actual model's prediction
    MODEL_PREDICTION.labels(str(prediction)).inc()
    
    return {
        "prediction": prediction,
        "features_used": input_df.to_dict(orient="records")[0],
        "real_inference": True
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

