import requests

url = "https://sandbox.api.getsafepay.com/client/plans/v1/"

payload = "{\n    \"amount\": \"100\",\n    \"currency\": \"PKR\",\n    \"interval\": \"MONTH\",\n    \"type\": \"RECURRING\",\n    \"interval_count\": 1,\n    \"product\": \"bananas\",\n    \"active\": true\n}"
headers = {}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
