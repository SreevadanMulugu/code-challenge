# 1. Clone the repo
git clone <your-repo> && cd <your-repo>

# 2. Build & start everything
docker compose up -d   # first run will download ~6-7 GB model, afterwards it's cached

# 3. Attach
docker compose exec app bash
#   └─ You are now inside /app. Run python, jupyter lab, or your Streamlit/FastAPI app.

# 4. (optional) open in VS Code
code .   # with the Remote-Containers extension it auto-attaches