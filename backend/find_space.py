from gradio_client import Client
import time

candidates = [
    "google/sdxl",
    "stabilityai/stable-diffusion-xl-base-1.0",
    "stabilityai/stable-diffusion-2-1", 
    "ByteDance/SDXL-Lightning",
    "fal/flux-fast" 
]

def test_candidate(space_id):
    print(f"\n--- Testing {space_id} ---")
    try:
        client = Client(space_id)
        print("Connected.")
        
        # Try generic predict
        try:
            result = client.predict(
                "A cute cat",
                api_name="/predict"
            )
            print("Success with /predict!")
            return True
        except:
            pass
            
        try:
            result = client.predict(
                "A cute cat",
                api_name="/run"
            )
            print("Success with /run!")
            return True
        except:
            pass
            
        try:
            # Try to infer endpoint from view_api (not implemented here, just blindly trying common ones)
             result = client.predict(
                "A cute cat", 
                "low quality", 
                True, 0, 1024, 1024, 3, 8, True, 
                api_name="/run"
            )
             print("Success with /run (complex args)!")
             return True
        except:
            pass
            
        print("Failed to predict.")
        
    except Exception as e:
        print(f"Connection Failed: {e}")
    return False

for c in candidates:
    if test_candidate(c):
        print(f"WINNER: {c}")
        break
