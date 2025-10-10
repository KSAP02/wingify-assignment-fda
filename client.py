import requests
import os

API_URL = "http://localhost:8000/analyze"

def test_analysis():
    # Point to a file already in your data/ folder
    file_path = r"data\TSLA-Q2-2025-Update.pdf"
    if not os.path.exists(file_path):
        print(f"ERROR: Test file {file_path} not found.")
        return

    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"query": "Summarize the financial performance and risks in this document"}
        response = requests.post(API_URL, files=files, data=data)

    if response.status_code == 200:
        print("✅ Request successful!")
        print("Response JSON:\n")
        print(response.json())
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    test_analysis()
