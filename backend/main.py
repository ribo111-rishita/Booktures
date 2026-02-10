from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import base64
import random
import time
import urllib.parse
import os
import io
import re
from gradio_client import Client
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load from parent directory (where .env is)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '..', '.env')
load_dotenv(env_path)

app = FastAPI()
print("Force reload triggered...", flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
def generate_image(data: ImageRequest):
    prompt = data.prompt.strip()

    print(f"Received Prompt: {prompt}", flush=True)

    try:
        # Clean prompt (user text)
        cleaned = re.sub(r'[^\w\s\.,\']', '', prompt)
        truncated = cleaned[:300] # Increased limit slightly for context
        
        # User's detailed prompt template
        final_prompt = (
            f"Create a clear, detailed children's storybook illustration representing the following text: '{truncated}'. "
            "Focus only on visible objects, people, setting, lighting and actions. "
            "Avoid text, captions or watermarks. Use a colorful, cute style."
        )
        encoded_prompt = urllib.parse.quote(final_prompt)
        
        # --- LAYER 0: Google Gemini (Imagen 3/4) ---
        # Disabled due to billing requirements.
        # gemini_key = os.getenv("GEMINI_API_KEY") ... (logic removed)
        print("Layer 0: Gemini Disabled for Performance", flush=True)

        # --- LAYER 1: HF Inference API (Authenticated) ---
        # --- LAYER 1: HF Inference API (Disabled/402) ---
        # User has no credits.
        print("Layer 1: Disabled (Quota Exceeded)", flush=True)

        # --- LAYER 2: HuggingFace SDXL-Flash (Primary) ---
        print("Layer 2: Trying SDXL-Flash (Gradio)...", flush=True)
        try:
             client = Client("KingNish/SDXL-Flash")
             
             # Simplify prompt for Flash model (distilled models prefer direct instruction)
             flash_prompt = f"Cinematic, photorealistic, highly detailed, 8k resolution. {truncated}"
             
             # Function /run takes: prompt, negative_prompt, use_negative_prompt, seed, width, height, guidance_scale, num_inference_steps, randomize_seed
             result = client.predict(
                flash_prompt, 
                "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation, NSFW, text, watermark", # negative_prompt
                True, # use_negative_prompt
                0, # seed (randomized anyway)
                1024, # width
                1024, # height
                3.0, # guidance_scale (Flash default)
                8, # num_inference_steps
                True, # randomize_seed
                api_name="/run"
             )
             
             gallery = result[0]
             if gallery and len(gallery) > 0:
                 first_image = gallery[0]
                 image_path = None
                 if isinstance(first_image, dict):
                     if 'image' in first_image:
                         img_val = first_image['image']
                         if isinstance(img_val, dict) and 'path' in img_val:
                             image_path = img_val['path']
                         elif isinstance(img_val, str):
                             image_path = img_val
                 elif isinstance(first_image, str): 
                     image_path = first_image
                     
                 if not image_path and 'image' in first_image:
                     image_path = first_image['image']

                 if image_path:
                     with open(image_path, "rb") as img_file:
                         img_data = img_file.read()
                         base64_str = base64.b64encode(img_data).decode('utf-8')
                         data_url = f"data:image/webp;base64,{base64_str}"
                         print("Success with Layer 2 (SDXL-Flash)", flush=True)
                         return {"imageUrl": data_url}

        except Exception as e:
            print(f"Layer 2 Failed: {e}", flush=True)


        # --- LAYER 3: Fallback (Placeholder) ---
        print("Layer 3: Using Fallback Placeholder.", flush=True)
        fallback_url = "https://dummyimage.com/768x1024/faebd7/000000.png?text=AI+Generating+Failed"
        try:
             response = requests.get(fallback_url, timeout=10, verify=False)
             if response.status_code == 200:
                img_data = response.content
                base64_str = base64.b64encode(img_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_str}"
                return {"imageUrl": data_url}
        except Exception as e:
            print(f"Fallback failed too: {e}", flush=True)
            
        return {"imageUrl": None}

    except Exception as e:
        import traceback
        print(f"Error in generate_image: {e}\n{traceback.format_exc()}", flush=True)
        return {"imageUrl": None}

@app.get("/")
def root():
    return {"status": "ok"}
