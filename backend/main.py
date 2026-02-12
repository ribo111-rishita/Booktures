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
import google.generativeai as genai

from dotenv import load_dotenv

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


# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def refine_prompt_with_gemini(text):
    print("Refining prompt with Gemini...", flush=True)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt_template = (
            f"Analyze the following text from a book and create a highly detailed, cinematic visual prompt "
            f"for an AI image generator. Focus on the main subject, setting, lighting, mood, and artistic style. "
            f"The output must be a single paragraph of descriptive text suitable for Stable Diffusion. "
            f"Do not include any intro/outro text, just the prompt itself.\n\n"
            f"Text: {text}\n\n"
            f"Visual Prompt:"
        )
        
        response = model.generate_content(prompt_template)
        refined_prompt = response.text.strip()
        print(f"Gemini Refined Prompt: {refined_prompt[:100]}...", flush=True)
        return refined_prompt
    except Exception as e:
        print(f"Gemini Refinement Failed: {e}. Falling back to original text.", flush=True)
        return text

@app.post("/generate-image")
def generate_image(data: ImageRequest):
    prompt = data.prompt.strip()

    print(f"Received Prompt: {prompt}", flush=True)

    try:
        # Step 1: Refine prompt with Gemini
        final_prompt = refine_prompt_with_gemini(prompt)
        
        # Ensure it's not too long for the image APIs (some have limits, but 1000ish is usually fine)
        truncated = final_prompt[:1000]
        
        encoded_prompt = urllib.parse.quote(truncated)
        
        print(f"Layer 1: Trying SDXL-Flash with prompt: {truncated[:100]}...", flush=True)
        
        max_retries = 3
        layer1_success = False
        
        for attempt in range(max_retries):
            try:
                 client = Client("KingNish/SDXL-Flash")
                 flash_prompt = f"Cinematic, photorealistic, highly detailed, 8k resolution. {truncated}"
                 
                 print(f"Layer 1 (SDXL-Flash) Attempt {attempt+1}/{max_retries} - Sending request...", flush=True)
                 
                 result = client.predict(
                    flash_prompt, 
                    "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation, NSFW, text, watermark", 
                    True, 0, 896, 1152, 3.0, 8, True, 
                    api_name="/run"
                 )
                 
                 print(f"Layer 1 (SDXL-Flash) Attempt {attempt+1} - Request successful. Processing result...", flush=True)
                 
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
                         print(f"Layer 1 (SDXL-Flash) - Image path found: {image_path}", flush=True)
                         with open(image_path, "rb") as img_file:
                             img_data = img_file.read()
                             base64_str = base64.b64encode(img_data).decode('utf-8')
                             data_url = f"data:image/webp;base64,{base64_str}"
                             print(f"Success with Layer 1 (SDXL-Flash) on attempt {attempt+1}", flush=True)
                             return {"imageUrl": data_url}
                     else:
                         print("Layer 1 (SDXL-Flash) - No valid image path in response.", flush=True)

            except Exception as e:
                print(f"Layer 1 Failed (Attempt {attempt+1}/{max_retries}): {e}", flush=True)
                if "quota" in str(e).lower() and attempt < max_retries - 1:
                    print("Quota hit. Waiting 20s before retry...", flush=True)
                    time.sleep(20)
            
        print("Layer 1 Failed: All retries exhausted.", flush=True)

        print(f"Layer 2: Trying FLUX.1-schnell with prompt: {truncated[:100]}...", flush=True)
        try:
            client = Client("black-forest-labs/FLUX.1-schnell")
            print("Layer 2 (FLUX.1-schnell) - Sending request...", flush=True)
            
            # FLUX.1-schnell API signature usually involves prompt, seed, randomize_seed, width, height, num_inference_steps
            # We will try the standard /infer endpoint
            result = client.predict(
                    prompt=truncated,
                    seed=0,
                    randomize_seed=True,
                    width=896,
                    height=1152,
                    num_inference_steps=4,
                    api_name="/infer"
            )
            
            print("Layer 2 (FLUX.1-schnell) - Request successful. Processing result...", flush=True)
            
            # Result is usually a tuple or filepath
            if result:
                image_path = result
                if isinstance(result, tuple) or isinstance(result, list):
                    image_path = result[0]
                
                # Check strict dictionary structure if needed, but usually it returns a path info
                if isinstance(image_path, dict) and 'image' in image_path:
                    image_path = image_path['image']
                    
                if image_path and isinstance(image_path, str) and os.path.exists(image_path):
                     print(f"Layer 2 (FLUX.1-schnell) - Image path found: {image_path}", flush=True)
                     with open(image_path, "rb") as img_file:
                         img_data = img_file.read()
                         base64_str = base64.b64encode(img_data).decode('utf-8')
                         data_url = f"data:image/webp;base64,{base64_str}"
                         print(f"Success with Layer 2 (FLUX.1-schnell)", flush=True)
                         return {"imageUrl": data_url}
                else:
                    print(f"Layer 2 (FLUX.1-schnell) - Invalid result format: {result}", flush=True)

        except Exception as e:
            print(f"Layer 2 Failed: {e}", flush=True)


        print("Layer 3: Trying Pollinations AI (Backup)...", flush=True)
        try:
             seed = random.randint(0, 100000)
             
             poll_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=896&height=1152&seed={seed}&nologo=true&model=flux"
             
             response = requests.get(poll_url, timeout=25)
             
             is_rate_limit = False
             if len(response.content) in [74444, 74445, 74443]: 
                  import hashlib
                  md5 = hashlib.md5(response.content).hexdigest()
                  if md5 == "821b5efedc9ea8d6a498ab1b43bc569e":
                      is_rate_limit = True

             if response.status_code == 200 and len(response.content) > 5000 and not is_rate_limit:
                 img_data = response.content
                 base64_str = base64.b64encode(img_data).decode('utf-8')
                 data_url = f"data:image/jpeg;base64,{base64_str}"
                 print("Success with Layer 3 (Pollinations AI)", flush=True)
                 return {"imageUrl": data_url}
             else:
                 print(f"Pollinations returned status {response.status_code} or Rate Limit image.", flush=True)

        except Exception as e:
            print(f"Layer 2 Failed: {e}", flush=True)


        print("Layer 3: Generating Local Placeholder (Network-Free).", flush=True)
        try:
             from PIL import Image, ImageDraw
             
             width, height = 896, 1152
             img = Image.new('RGB', (width, height), color = (40, 44, 52)) 
             d = ImageDraw.Draw(img)
             
             d.rectangle([20, 20, width-20, height-20], outline=(0, 255, 136), width=5)
             d.line([20, 20, width-20, height-20], fill=(0, 255, 136), width=2)
             d.line([20, height-20, width-20, 20], fill=(0, 255, 136), width=2)
             
             buffered = io.BytesIO()
             img.save(buffered, format="JPEG")
             img_str = base64.b64encode(buffered.getvalue()).decode()
             data_url = f"data:image/jpeg;base64,{img_str}"
             return {"imageUrl": data_url}
             
        except Exception as e:
             print(f"Local Fallback Failed: {e}", flush=True)
            
        return {"imageUrl": None}

    except Exception as e:
        import traceback
        print(f"Error in generate_image: {e}\n{traceback.format_exc()}", flush=True)
        return {"imageUrl": None}

@app.get("/")
def root():
    return {"status": "ok"}

