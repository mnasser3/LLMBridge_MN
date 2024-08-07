import requests

url = 'https://metal-dancers-type.loca.lt/predict'
data = {'input_text': "'DB SL RDL', 'KB Swing - Bridge', 'KB Front Squat'"}  # arms

try:
    # Set a long timeout to see if the server eventually responds
    response = requests.post(url, json=data, timeout=1200)  # 2 minutes timeout
    
    # Check if the response status code indicates success
    if response.status_code == 200:
        try:
            response_json = response.json()
            # Check if 'output_text' is in the response JSON
            if 'output_text' in response_json:
                print(response_json['output_text'])
            else:
                print("Key 'output_text' not found in the response JSON.")
        except requests.exceptions.JSONDecodeError:
            print("Failed to decode JSON. Response content:", response.text)
    else:
        print(f"Request failed with status code: {response.status_code}")
        print("Response content:", response.text)

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
