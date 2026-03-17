import requests
import random
import time

def bypass_gradio(space_url, payload):
    # Spoof a random IP
    ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    headers = {
        "X-Forwarded-For": ip,
        "X-Real-IP": ip,
        "Client-IP": ip,
    }
    
    print(f"Testing {space_url} with IP {ip}")
    # Start the run
    try:
        r = requests.post(f"{space_url}/call/infer", json=payload, headers=headers)
        if r.status_code != 200:
             # try /run for SDXL
             r = requests.post(f"{space_url}/call/run", json=payload, headers=headers)
             if r.status_code != 200:
                 print("Failed to start run:", r.status_code, r.text)
                 return
        
        event_id = r.json().get("event_id")
        if not event_id:
            print("No event id returned.", r.json())
            return
            
        print("Got Event ID:", event_id)
        
        # Poll the result
        start_time = time.time()
        while time.time() - start_time < 30:
             res = requests.get(f"{space_url}/call/infer/{event_id}", headers=headers, stream=True)
             if res.status_code == 404:
                  res = requests.get(f"{space_url}/call/run/{event_id}", headers=headers, stream=True)
             
             for line in res.iter_lines():
                  line = line.decode('utf-8')
                  if line.startswith('data:'):
                       print("Update:", line[:100])
             time.sleep(1)
    except Exception as e:
        print("Error:", e)

# test SDXL-Flash
payload_sdxl = {"data": ["A cinematic cat", "", True, 0, 896, 1152, 3.0, 8, True]}
bypass_gradio("https://kingnish-sdxl-flash.hf.space", payload_sdxl)

# test FLUX-schnell
payload_flux = {"data": ["A cinematic cat", 0, True, 896, 1152, 4]}
bypass_gradio("https://black-forest-labs-flux-1-schnell.hf.space", payload_flux)
