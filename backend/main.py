from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
def generate_image(data: ImageRequest):
    prompt = data.prompt.strip()

    if not prompt:
        return {"imageUrl": None}

    encoded = urllib.parse.quote(prompt[:300])

    image_url = (
        "https://image.pollinations.ai/prompt/"
        + encoded
        + "?width=512&height=512&seed=42"
    )

    return {"imageUrl": image_url}

@app.get("/")
def root():
    return {"status": "ok"}
