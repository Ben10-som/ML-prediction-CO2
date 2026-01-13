import requests
import json

url = "http://localhost:8000/predict"
data = {
    "NumberofFloors": 5,
    "NumberofBuildings": 1,
    "Age": 20.0,
    "ENERGYSTARScore": 85.0,
    "PrimaryPropertyType": "Office",
    "BuildingType": "NonResidential",
    "Neighborhood": "DOWNTOWN",
    "Latitude": 47.6038,
    "Longitude": -122.3301,
    "Has_Parking": 1,
    "Has_Gas": 1,
    "Has_Steam": 0,
    "PropertyGFATotal": 50000.0,
    "PropertyGFAParking": 5000.0
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=4)}")
except Exception as e:
    print(f"Error testing prediction: {e}")
