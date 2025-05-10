from fastapi import FastAPI
from routers import analyze, reward, chatbot

app = FastAPI()

@app.get("/")
def root():
    return {'Hello':'World!'} 

## Router
app.include_router(analyze.router, prefix="/ai")
app.include_router(reward.router, prefix="/ai")
app.include_router(chatbot.router, prefix="/ai")