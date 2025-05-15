# DearMind-AI

FastAPI based AI Model Server for DearMind - Google Solution Challenge 2025

---

## Project Description
🎨 AI API for DearMind, an emotion-based arts therapy service

## Project Setup

### Run Locally
1. **Clone Repository & Build Your VENV**
```bash
git clone https://github.com/osh925/dearmind-ai.git
cd dearmind-ai
conda create -n YOUR_VENV_NAME
pip install -r requirements.txt
```
2. **Setup your environment variables**
```bash
# You will need your own credential file.
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
```
3. **Run your local server**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
1. **Clone Repository**
```bash
git clone https://github.com/your-org/dearmind-ai.git
cd dearmind-ai
```
2. **Docker Image Build**
```bash
git clone https://github.com/your-org/dearmind-ai.git
cd dearmind-ai
```
3. **Initiate Local Container**
```bash
# If you have your GOOGLE_APPLICATION_CREDENTIALS file locally
docker run -d \
-p 8000:8080 \
-v /path/to/key.json:/secrets/key.json:ro \
-e GOOGLE_APPLICATION_CREDENTIALS=/secrets/key.json \
dearmind-ai

# If you already have your credential values mounted in your environment variable
# For Linux & Mac
docker run -d -p 8000:8080 -v ~/.config/gcloud:/root/.config/gcloud dearmind-ai

# For Windows
docker run d -p 8000:8080 -v ${HOME}\.config\gcloud:/root/.config/gcloud my-image-name
```

### Deployment (Cloud Run)
1. **Push Docker Image to Artifact Registry**
```bash
docker tag dearmind-ai \
    us-central1-docker.pkg.dev/<PROJECT_ID>/dearmind-ai-repo/dearmind-ai:latest

docker push us-central1-docker.pkg.dev/<PROJECT_ID>/dearmind-ai-repo/dearmind-ai:latest
```
2. **Deploy via Google Cloud Run**
```bash
# Cloud Run Deployment
gcloud run deploy dearmind-ai \
--image=us-central1-docker.pkg.dev/<PROJECT_ID>/dearmind-ai-repo/dearmind-ai:latest \
--region=us-central1 \
--platform=managed \
--service-account=<YOUR_SA>@<PROJECT_ID>.iam.gserviceaccount.com \
--allow-unauthenticated
```