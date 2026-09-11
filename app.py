import json
import os
import time
import requests
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)


@app.route("/")
def index():
  return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>MCHLERN Toolkit - Roblox Uploader</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>MCHLERN Toolkit / Uploader to Roblox</h2>
            <form action="/upload-to-roblox" method="POST" enctype="multipart/form-data">
                <label>API Key Roblox:</label><br>
                <input type="password" name="api_key" style="width: 300px;" required><br><br>
                
                <label>User ID / Group ID:</label><br>
                <input type="text" name="user_id" style="width: 300px;" required><br><br>
                
                <label>Asset Type:</label><br>
                <select name="asset_type">
                    <option value="Decal">Decal</option>
                    <option value="Audio">Audio</option>
                    <option value="Model">Model</option>
                </select><br><br>
                
                <label>Display Name:</label><br>
                <input type="text" name="display_name" value="Asset Toolkit" style="width: 300px;" required><br><br>
                
                <label>File (Gambar/Audio):</label><br>
                <input type="file" name="file" required><br><br>
                
                <button type="submit">Upload ke Roblox</button>
            </form>
        </body>
        </html>
    """)


@app.route("/upload-to-roblox", methods=["POST"])
def upload_to_roblox():
  api_key = request.form.get("api_key")
  user_id = request.form.get("user_id")
  asset_type = request.form.get("asset_type", "Decal")
  display_name = request.form.get("display_name", "MCHLERN Asset")
  description = request.form.get("description", "Uploaded via MCHLERN Toolkit")

  if "file" not in request.files:
    return jsonify({"error": "No file part provided"}), 400

  file = request.files["file"]
  if file.filename == "":
    return jsonify({"error": "No selected file"}), 400

  metadata = {
      "assetType": asset_type,
      "displayName": display_name,
      "description": description,
      "creationContext": {"creator": {"userId": str(user_id)}},
  }

  url = "https://apis.roblox.com/assets/v1/assets"
  headers = {"x-api-key": api_key}

  files = {
      "request": (None, json.dumps(metadata), "application/json"),
      "fileData": (file.filename, file.read(), file.content_type),
  }

  try:
    response = requests.post(url, headers=headers, files=files)

    if response.status_code not in [200, 202]:
      return (
          jsonify(
              {
                  "error": "Failed to initiate upload",
                  "details": response.text,
              }
          ),
          response.status_code,
      )

    operation_data = response.json()
    operation_path = operation_data.get("path")

    if not operation_path:
      return (
          jsonify(
              {
                  "error": "Invalid response from Roblox, missing operation path",
                  "response": operation_data,
              }
          ),
          500,
      )

    poll_url = f"https://apis.roblox.com/cloud/v2/{operation_path}"
    max_retries = 15
    asset_id = None

    for _ in range(max_retries):
      time.sleep(3)
      poll_response = requests.get(poll_url, headers=headers)

      if poll_response.status_code == 200:
        poll_result = poll_response.json()
        if poll_result.get("done", False):
          asset_id = poll_result.get("response", {}).get(
              "assetId"
          ) or poll_result.get("response", {}).get("asset_id")
          break

    if asset_id:
      return (
          jsonify(
              {
                  "success": True,
                  "message": "Asset successfully uploaded!",
                  "assetId": asset_id,
                  "assetUrl": f"https://www.roblox.com/library/{asset_id}",
              }
          ),
          200,
      )
    else:
      return (
          jsonify(
              {
                  "error": (
                      "Upload timed out or processing failed on Roblox side."
                  )
              }
          ),
          500,
      )

  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
