"""Fetch the pinned dsh-pet animation preview (CC BY-NC-SA 4.0)."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

REVISION = "fb38ce620576f5ed3735a99536d2b1a4a9eb313f"
BASE = f"https://raw.githubusercontent.com/PC2005-cloud/dsh-pet/{REVISION}/dsh-pet/assets/webm/"
DEST = Path(__file__).resolve().parents[1] / "src" / "cyber_habitat" / "whale_preview"
CLIPS = {
    "idle": "待机呼吸休闲",
    "greeting": "女仆屈膝礼仪",
    "thinking": "深度思考碎碎念",
    "sleepy": "原地小憩沉眠",
}
MAX_BYTES = 16 * 1024 * 1024


def download(clip: tuple[str, str]) -> None:
    state, name = clip
    target = DEST / f"{state}.webm"
    for attempt in range(3):
        try:
            with urlopen(BASE + quote(name + ".webm"), timeout=20) as response:
                data = response.read(MAX_BYTES + 1)
            break
        except (URLError, TimeoutError) as error:
            if attempt == 2 or isinstance(error, HTTPError) and error.code < 500:
                raise
            sleep(attempt + 1)
    if not data.startswith(b"\x1a\x45\xdf\xa3") or len(data) > MAX_BYTES:
        raise ValueError(f"Invalid WebM preview: {state}")
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(data)
    temporary.replace(target)
    print(f"{target.name}: {len(data):,} bytes")


if __name__ == "__main__":
    DEST.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=len(CLIPS)) as pool:
        list(pool.map(download, CLIPS.items()))
