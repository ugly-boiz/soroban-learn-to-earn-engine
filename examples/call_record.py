import requests

value = 123.45
resp = requests.post("http://localhost:8000/record_on_chain", json={"value": value})
print("status", resp.status_code)
print(resp.json())
