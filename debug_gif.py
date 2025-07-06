import asyncio
import io
import aiohttp
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

async def generate_radar_gif():
    """Fetches radar images and generates an animated GIF."""
    image_urls = [f"https://sojpublicdata.blob.core.windows.net/jerseymet/Radar{i:02d}.JPG" for i in range(1, 11)]

    async def fetch_image(session, url):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
        except aiohttp.ClientError as e:
            _LOGGER.warning(f"Failed to fetch {url}: {e}")
        return None

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_image(session, url) for url in image_urls]
        image_data = await asyncio.gather(*tasks)

    images = [Image.open(io.BytesIO(data)) for data in image_data if data]

    if not images:
        _LOGGER.error("Could not download any radar images.")
        return

    buffer = io.BytesIO()
    images[0].save(
        buffer,
        format='GIF',
        save_all=True,
        append_images=images[1:],
        duration=500,
        loop=0
    )

    gif_bytes = buffer.getvalue()
    _LOGGER.info(f"Generated GIF bytes (first 10): {gif_bytes[:10]}")

    with open("debug_radar.gif", "wb") as f:
        f.write(gif_bytes)
    _LOGGER.info("Saved generated GIF to debug_radar.gif")

if __name__ == "__main__":
    asyncio.run(generate_radar_gif())