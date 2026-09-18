from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>CloudGuard Preview</title>
        <style>
            body {
                font-family: Arial;
                background: #0f172a;
                color: white;
                text-align: center;
                padding-top: 100px;
            }
            .card {
                max-width: 550px;
                margin: auto;
                padding: 35px;
                background: #1e293b;
                border-radius: 15px;
            }
            h1 { color: #38bdf8; }
            .status { color: #4ade80; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>CloudGuard Preview Environment</h1>
            <h3 class="status">● Application Running</h3>
            <p>This app is running inside a temporary Docker preview container.</p>
        </div>
    </body>
    </html>
    """

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "cloudguard-preview",
        "container": os.getenv("HOSTNAME", "unknown")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
