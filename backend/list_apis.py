from gradio_client import Client

spaces = [
    "KingNish/SDXL-Flash",
    "ByteDance/Hyper-SD",
    "playgroundai/playground-v2.5-1024px-aesthetic",
    "ehristoforu/dalle-3-xl" # sometimes works
]

for s in spaces:
    print(f"\n--- Testing {s} ---")
    try:
        client = Client(s)
        print("Connected!")
        client.view_api()
    except Exception as e:
        print(f"Error: {e}")
