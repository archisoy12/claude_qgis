import os
import asyncio
import httpx
from typing import Optional, Tuple

KAKAO_API_KEY = os.environ.get("KAKAO_API_KEY", "")
KAKAO_URL     = "https://dapi.kakao.com/v2/local/search/address.json"


async def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """주소 문자열을 (lat, lng) 좌표로 변환. 실패 시 None 반환."""
    if not KAKAO_API_KEY:
        return None

    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params  = {"query": address, "analyze_type": "similar"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(KAKAO_URL, headers=headers, params=params)
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if not docs:
                return None
            doc = docs[0]
            return float(doc["y"]), float(doc["x"])  # lat, lng
        except Exception:
            return None


async def batch_geocode(addresses: list[str], delay: float = 0.1) -> dict[str, Optional[Tuple[float, float]]]:
    """여러 주소를 순차적으로 지오코딩. Kakao API rate limit 대응."""
    results = {}
    for addr in addresses:
        results[addr] = await geocode_address(addr)
        await asyncio.sleep(delay)
    return results
