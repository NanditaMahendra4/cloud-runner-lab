# Cloud Runner Basic Lab

This lab deploys a containerized Flask application on Google Cloud Run, then monitors and scales it. It builds on the original beginner lab with an improved app, an updated base image, and fixes needed to build and deploy successfully today (including from an Apple Silicon Mac).

---

## Changes from the Original Lab

**Application (`app.py`)**
- **Configurable greeting:** the homepage message is read from a `GREETING` environment variable, so it can be changed in Cloud Run without editing code.
- **Styled HTML homepage** with links to the service's other endpoints, replacing the plain "Hello, World!" text.
- **`GET /info` endpoint** that returns the Cloud Run service and revision name, using the `K_SERVICE` and `K_REVISION` variables Cloud Run sets automatically.
- **Structured JSON logging:** every request is logged as JSON with a severity, path, and status code, so it can be filtered in Cloud Logging.
- **Reads the `PORT` environment variable** (as Cloud Run recommends) instead of hard-coding 8080.
- **`debug=False`** so the Flask debugger is never exposed.

**Container (`Dockerfile`)**
- **Upgraded the base image from Python 3.8 to Python 3.12.** Python 3.8 no longer receives security updates.

---

## Project Structure

```
.
├── app.py        # Flask application
├── Dockerfile    # Container definition
└── README.md
```
---

## Step-by-Step Guide

### Step 1: Set Up a Google Cloud Project

1. **Create a project** in the [Google Cloud Console](https://console.cloud.google.com/) (e.g. `cloud-runner-lab`).
   - Note the **project ID** shown in the project picker. It is often different from the name, e.g. `cloud-runner-lab-123456`.

2. **Log in and select the project:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Enable the required APIs:**
   ```bash
   - In the Console, navigate to APIs & Services > Library.
   - Enable the Cloud Run API and the Container Registry API.
   ```

---

### Step 2: Build the Container Image and 

1. **Create the Flask Application**:
   - Write a Flask application in Python that serves an HTML homepage with a configurable greeting, an `/info` endpoint that reports the Cloud Run service and revision, and structured JSON request logging.
   - `app.py`:
```python
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
```
    
2.  **Dockerfile:**
   ```Dockerfile
   FROM python:3.12-slim

   WORKDIR /app
   COPY . /app
   RUN pip install flask

   EXPOSE 8080
   CMD ["python", "app.py"]
   ```

3. **Build the image**, from the folder containing `app.py` and `Dockerfile`:
   ```bash
   docker build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/hello-world .
   ```
   - The project ID must be lowercase.
   - The `.` at the end is required. It tells Docker to build from the current folder.

4. **Test it locally (optional):**
   ```bash
   docker run -p 8080:8080 gcr.io/YOUR_PROJECT_ID/hello-world
   ```
---

### Step 3: Push the Image

1. **Let Docker authenticate with Google Cloud:**
   ```bash
   gcloud auth configure-docker
   ```

2. **Push the image:**
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/hello-world
   ```
---

### Step 4: Deploy to Cloud Run

1. In the Console, go to **Cloud Run** and click **Create service**.
2. Select **Deploy one revision from an existing container image** and enter `gcr.io/YOUR_PROJECT_ID/hello-world:latest`, or click **Select** and find it under Artifact Registry.
3. Set a **service name** (e.g. `hello-world`) and the region `us-central1`.
4. Under **Authentication**, choose **Allow public access**.
5. Under **Containers > Variables**, add `GREETING` with a custom message (optional).
6. Click **Create**. When it finishes, Cloud Run shows the service URL.

**Redeploying after changes:** rebuild and push the image, then open the service, select the new `latest` image in the **Containers** tab, and click **Redeploy**.
---

### Step 5: Test the Application

Open the service URL and check each endpoint:
- `/` shows the greeting page
- `/info` returns the service and revision name. The revision changes with each deploy.

---

### Step 6: Monitor and Scale

1. **Metrics:** the service's **Observability > Metrics** tab shows request count, latency, and memory usage.
2. **Logs:** the **Logs** tab shows the structured request logs. Since they are JSON, they can be filtered by field, for example:
   ```
   jsonPayload.path="/info"
   ```
3. **Scaling:** Cloud Run scales automatically, down to zero when there is no traffic. Minimum and maximum instances can be set in the **Scaling** tab. Keep the minimum at 0 to avoid charges.

---

## Conclusion

In this lab I:
- Set up a Google Cloud project and enabled the required APIs.
- Extended the Flask app with a configurable greeting and info endpoints, and structured logging.
- Upgraded the container to Python 3.12 and built it for Cloud Run's amd64 platform.
- Pushed the image, deployed it to Cloud Run, and accessed it through a public URL.
- Monitored the service with metrics and structured logs, and configured scaling.
