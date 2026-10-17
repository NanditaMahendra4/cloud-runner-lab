import json
import os

from flask import Flask, jsonify, request

app = Flask(__name__)

GREETING = os.environ.get("GREETING", "Hello from Cloud Run!")


@app.after_request
def log_request(response):
    print(json.dumps({
        "severity": "INFO",
        "message": "request handled",
        "path": request.path,
        "status": response.status_code,
    }), flush=True)
    return response


@app.route("/")
def home():
    return f"""
    <html>
      <head><title>Cloud Run Lab</title></head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 15%;">
        <h1>{GREETING}</h1>
        <p>Running on Google Cloud Run</p>
        <p><a href="/info">Service info</a></p>
      </body>
    </html>
    """


@app.route("/info")
def info():
    return jsonify(
        service=os.environ.get("K_SERVICE", "local"),
        revision=os.environ.get("K_REVISION", "local"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)