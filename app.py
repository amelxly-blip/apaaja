import os
import time
import json
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <title>MCHLERN Toolkit - Roblox Uploader</title>
        <style>
            body { background: #0f172a; color: #f8fafc; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); width: 400px; border: 1px solid #334155; }
            h2 { color: #38bdf8; text-align: center; margin-top: 0; }
            label { font-size: 13px; color: #94a3b8; display: block; margin-top: 10px; }
            input, select { width: 100%; padding: 10px; margin-top: 5px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
            button { width: 100%; background: #38bdf8; color: #0f0f0f; font-weight: bold; padding: 12px; border: none; border-radius: 6px; cursor: pointer; margin-top: 20px; }
            button:hover { background: #7dd3fc; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>MCHLERN Uploader</h2>
            <form action="/upload-to-roblox" method="POST" enctype="multipart/form-data">
                <label>Roblox API Key</label>
                <input type="password" name="api_key" required>
                
                <label>User ID / Group ID</label>
                <input type="text" name="user_id" required>
                
                <label>Tipe Aset</label>
                <select name="asset_type">
                    <option value="Decal">Decal</option>
                    <option value="Audio">Audio</option>
                    <option value="Model">Model</option>
                </select>
                
                <label>Nama Tampilan (Display Name)</label>
                <input type="text" name="display_name" value="MCHLERN Asset" required>
                
                <label>File (Audio/Gambar)</label>
                <input type="file" name="file" required>
                
                <button type="submit">Upload ke Roblox</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.route("/upload-to-roblox", methods=["POST"])
def upload_to_roblox():
    api_key = request.form.get("api_key")
    user_id = request.form.get("user_id")
    asset_type = request.form.get("asset_type", "Decal")
    display_name = request.form.get("display_name", "MCHLERN Asset")
    
    if "file" not in request.files:
        return jsonify({"error": "File tidak ditemukan"}), 400
    
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Nama file kosong"}), 400

    metadata = {
        "assetType": asset_type,
        "displayName": display_name,
        "description": "Uploaded via MCHLERN Toolkit",
        "creationContext": {"creator": {"userId": str(user_id)}}
    }

    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"x-api-key": api_key}
    files = {
        "request": (None, json.dumps(metadata), "application/json"),
        "fileData": (file.filename, file.read(), file.content_type)
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        if response.status_code not in [200, 202]:
            return jsonify({"error": "Gagal memulai upload", "details": response.text}), response.status_code

        operation_path = response.json().get("path")
        if not operation_path:
            return jsonify({"error": "Path operasi Roblox tidak valid", "response": response.json()}), 500

        poll_url = f"https://apis.roblox.com/cloud/v2/{operation_path}"
        asset_id = None
        
        for _ in range(15):
            time.sleep(3)
            poll_resp = requests.get(poll_url, headers=headers)
            if poll_resp.status_code == 200:
                poll_data = poll_resp.json()
                if poll_data.get("done", False):
                    asset_id = poll_data.get("response", {}).get("assetId") or poll_data.get("response", {}).get("asset_id")
                    break

        if asset_id:
            return jsonify({"success": True, "assetId": asset_id, "url": f"https://www.roblox.com/library/{asset_id}"})
        return jsonify({"error": "Timeout saat menunggu proses verifikasi Roblox"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
