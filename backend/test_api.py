from gradio_client import Client

try:
    print("Testing stable-diffusion-3-medium...")
    client = Client("stabilityai/stable-diffusion-3-medium")
    result = client.predict(
        prompt="A cinematic cat",
        negative_prompt="",
        seed=0,
        randomize_seed=True,
        width=1024,
        height=1024,
        guidance_scale=5,
        num_inference_steps=28,
        api_name="/infer"
    )
    print("Success!", result)
except Exception as e:
    print(e)
