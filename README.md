# Cloud Runner Basic Lab

This lab deploys a containerized Flask application on Google Cloud Run, then monitors and scales it. It builds on the original beginner lab with an improved app, an updated base image, and fixes needed to build and deploy successfully today (including from an Apple Silicon Mac).

---

## Changes from the Original Lab

**Application (`app.py`)**
- **Configurable greeting:** the homepage message is read from a `GREETING` environment variable, so it can be changed in Cloud Run without editing code.
- **Styled HTML homepage** with links to the service's other endpoints, replacing the plain "Hello, World!" text.
- **`GET /health` endpoint** that returns `{"status": "ok"}` with a 200, giving Cloud Run and monitoring tools a lightweight endpoint to check.
- **`GET /info` endpoint** that returns the Cloud Run service and revision name, using the `K_SERVICE` and `K_REVISION` variables Cloud Run sets automatically.
- **Structured JSON logging:** every request is logged as JSON with a severity, path, and status code, so it can be filtered in Cloud Logging.
- **Reads the `PORT` environment variable** (as Cloud Run recommends) instead of hard-coding 8080.
- **`debug=False`** so the Flask debugger is never exposed.

**Container (`Dockerfile`)**
- **Upgraded the base image from Python 3.8 to Python 3.12.** Python 3.8 no longer receives security updates.

**Build and deployment**
- **Built with `--platform linux/amd64`.** Images built on Apple Silicon Macs default to ARM, which Cloud Run cannot run.
- **Enabled the Artifact Registry API.** Google retired Container Registry, and `gcr.io` pushes are now stored in Artifact Registry.

---

## Project Structure

```
.
├── app.py        # Flask application
├── Dockerfile    # Container definition
└── README.md
```

## Endpoints

| Endpoint  | Description                                             |
|-----------|---------------------------------------------------------|
| `/`       | HTML homepage showing the configurable greeting         |
| `/health` | Health check, returns `{"status": "ok"}`                |
| `/info`   | Returns the Cloud Run service and revision name as JSON |

---

## Prerequisites

- A Google Cloud account with billing enabled (this lab stays within the free tier)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/), installed and running
- The [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (`gcloud`). On macOS without Homebrew, install it with:
  ```bash
  curl https://sdk.cloud.google.com | bash
  ```
  Then open a new terminal and check with `gcloud --version`.

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
   gcloud services enable run.googleapis.com artifactregistry.googleapis.com
   ```

---

### Step 2: Build the Container Image

1. **Dockerfile:**
   ```Dockerfile
   FROM python:3.12-slim

   WORKDIR /app
   COPY . /app
   RUN pip install flask

   EXPOSE 8080
   CMD ["python", "app.py"]
   ```

2. **Build the image**, from the folder containing `app.py` and `Dockerfile`:
   ```bash
   docker build --platform linux/amd64 -t gcr.io/YOUR_PROJECT_ID/hello-world .
   ```
   - The project ID must be lowercase.
   - The `.` at the end is required. It tells Docker to build from the current folder.

3. **Test it locally (optional):**
   ```bash
   docker run -p 8080:8080 gcr.io/YOUR_PROJECT_ID/hello-world
   ```
   Visit `http://localhost:8080`, `/health` and `/info`, then press `Ctrl+C` to stop.

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
   The push is finished when it prints a `latest: digest: sha256:...` line.

---

### Step 4: Deploy to Cloud Run

1. In the Console, go to **Cloud Run** and click **Create service**.
2. Select **Deploy one revision from an existing container image** and enter `gcr.io/YOUR_PROJECT_ID/hello-world:latest`, or click **Select** and find it under Artifact Registry.
3. Set a **service name** (e.g. `hello-world`) and the region `us-central1`.
4. Under **Authentication**, choose **Allow public access**.
5. Under **Containers > Variables**, add `GREETING` with a custom message (optional).
6. Click **Create**. When it finishes, Cloud Run shows the service URL.

**Redeploying after changes:** rebuild and push the image, then open the service, select the new `latest` image in the **Containers** tab, and click **Redeploy**.

**Command-line alternative:**
```bash
gcloud run deploy hello-world \
  --image gcr.io/YOUR_PROJECT_ID/hello-world \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GREETING="Hello from Cloud Run!"
```

---

### Step 5: Test the Application

Open the service URL and check each endpoint:
- `/` shows the greeting page
- `/health` returns `{"status": "ok"}`
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

## Troubleshooting

These are the problems encountered while completing this lab, and their fixes.

| Error | Cause and fix |
|-------|---------------|
| `zsh: command not found: docker` | Docker Desktop is not installed. Install it and open it. |
| `Docker Desktop is unable to start` | The engine was still starting. Wait for **Engine running** in Docker Desktop before building. |
| `repository name must be lowercase` | The `YOUR_PROJECT_ID` placeholder was left in. Replace it with the real, lowercase project ID. |
| `'docker buildx build' requires 1 argument` | The `.` at the end of `docker build` is missing. |
| `You do not currently have an active account selected` | Not logged in. Run `gcloud auth login`. |
| `Artifact Registry API has not been used in project...` | Enable it with `gcloud services enable artifactregistry.googleapis.com`. |
| `Container manifest ... must support amd64/linux` | The image was built for ARM on an Apple Silicon Mac. Rebuild with `--platform linux/amd64`, push, and redeploy. |
| `git push` rejected (`fetch first`) | The GitHub repo had a commit (e.g. a README) not present locally. Pull with `git pull origin main --allow-unrelated-histories --no-rebase --no-edit`, then push. |

---

## Cleanup

To avoid any charges after the lab:
- Delete the Cloud Run service (select it in Cloud Run and click **Delete**).
- Delete the image from Artifact Registry.
- Or shut down the whole project under **IAM & Admin > Settings**.

---

## Conclusion

In this lab I:
- Set up a Google Cloud project and enabled the required APIs.
- Extended the Flask app with a configurable greeting, health and info endpoints, and structured logging.
- Upgraded the container to Python 3.12 and built it for Cloud Run's amd64 platform.
- Pushed the image, deployed it to Cloud Run, and accessed it through a public URL.
- Monitored the service with metrics and structured logs, and configured scaling.
