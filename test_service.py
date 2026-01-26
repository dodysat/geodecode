import requests
import json
import sys

def test_conversion(lat, lon):
    url = f"http://localhost:8000/convert?latitude={lat}&longitude={lon}"
    print(f"Testing conversion for: {lat}, {lon}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Failed to connect to service: {e}")

if __name__ == "__main__":
    # Test specific coordinate from user
    test_conversion(-7.892473, 110.719908)
