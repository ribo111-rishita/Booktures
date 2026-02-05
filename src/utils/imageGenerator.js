export async function generateImageFromText(text) {
  try {
    if (!text || text.trim().length < 40) return null;

    const res = await fetch("http://127.0.0.1:8001/generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: text.slice(0, 500)
      })
    });

    if (!res.ok) return null;

    const data = await res.json();
    return data.imageUrl || null;
  } catch (err) {
    console.warn("Image generation failed:", err);
    return null;
  }
}
