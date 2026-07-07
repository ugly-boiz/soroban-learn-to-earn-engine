import requests

resp = requests.post("http://localhost:8000/predict", json={"batch_size": 2})
print("status", resp.status_code)
print(resp.json())
