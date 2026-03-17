from gradio_client import Client
import requests

spaces_to_test = [
    ("mukaist/Midjourney", "/run"),
    ("shreyas-h/Midjourney", "/infer"),
    ("John6666/flux-dev-schnell", "/infer"),
    ("prithivMLmods/Canopus-LoRA-Flux-Dev", "/infer"),
    ("multimodalart/flux-tarot-v1", "/infer"),
    ("awacke1/PollinationsAI", "/infer"),
    ("Purz/face-projection", "/infer"),
]

for space, api_name in spaces_to_test:
    print(f"\nTesting {space}...")
    try:
        client = Client(space)
        try:
             result = client.predict("a cinematic cat", api_name=api_name)
             print(f"Success {space}!", type(result))
        except Exception as e2:
             print(f"Failed {space} predict:", e2)
    except Exception as e:
        print(f"Failed {space} client load:", e)
