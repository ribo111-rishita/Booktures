from gradio_client import Client
import time
import os

def test_space(space_id, prompt):
    print(f"\nTesting {space_id}...")
    try:
        client = Client(space_id)
        start = time.time()
        
        # SDXL Lightning usually takes 'prompt' and 'negative_prompt' (or similar)
        # We need to inspect the API or just try the standard predict
        
        # Try view_api first to see what it expects
        # client.view_api() 
        
        # Most of these work with a simple string for prompt
        result = client.predict(
            prompt, # prompt
            "4step", # sampling method (specific to some lightning spaces) or just ignore
            api_name="/generate_image" # common endpoint, might vary
        )
        
        # If that fails, try generic /predict
        
        duration = time.time() - start
        print(f"Success! Time: {duration:.2f}s")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        # Try listing endpoints
        try:
            print("Trying to list API...")
            client = Client(space_id)
            client.view_api()
        except:
            pass
        return False

spaces = [
    "ByteDance/SDXL-Lightning",
    "artificialguybr/Stable-Diffusion-XL-Lightning",
    "stabilityai/stable-diffusion-2-1" 
]

for s in spaces:
    test_space(s, "A cute cat")
