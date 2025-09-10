"""
cctv_api.py

범용 한국 CCTV(도로 등) 연동 헬퍼 함수들.

설계 목표:
- 공공 API(예: 지자체 OpenAPI)로부터 카메라 목록(JSON)를 받아 스트림/스냅샷 URL 리스트로 변환
- 스냅샷 API를 폴링하여 OpenCV 프레임(numpy)로 변환
- GUI(예: gui_cctv.py)의 `add_stream()`에 바로 전달할 수 있는 URL 리스트 반환

주의:
- 공공 API 엔드포인트와 응답 포맷은 지역/기관마다 다릅니다. 아래 함수들은 "필드 이름("url_field")으로 URL을 추출하는 일반화된 방식"을 사용합니다.
"""
import io
import time
import requests
import numpy as np
from typing import List, Dict, Callable, Optional


def fetch_json(api_url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, timeout: float = 10.0) -> Dict:
    """단순한 GET JSON 요청 래퍼
    api_url: API 엔드포인트
    params: 쿼리 파라미터(예: 인증키, 페이지 등)
    """
    r = requests.get(api_url, params=params or {}, headers=headers or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def extract_urls_from_json(resp: Dict, array_path: List[str], url_field: str) -> List[str]:
    """JSON 응답에서 카메라 엔트리 리스트로 이동한 다음 각 엔트리의 url_field 값을 추출.

    array_path: JSON 루트에서 카메라 리스트까지의 키 경로 예: ["response", "data", "items"]
    url_field: 각 항목에서 URL을 담고 있는 필드명
    """
    cur = resp
    for k in array_path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return []

    if not isinstance(cur, list):
        return []

    urls = []
    for item in cur:
        if isinstance(item, dict) and url_field in item:
            urls.append(item[url_field])
    return urls


def fetch_camera_list_from_url(api_url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None,
                               array_path: Optional[List[str]] = None, url_field: str = "url") -> List[str]:
    """범용 카메라 목록 조회.

    - array_path가 None이면 최상위 리스트를 기대합니다.
    - url_field로 스트림/스냅샷 URL을 추출합니다.
    """
    j = fetch_json(api_url, params=params, headers=headers)
    if array_path:
        return extract_urls_from_json(j, array_path, url_field)
    # 최상위가 리스트인 경우
    if isinstance(j, list):
        urls = []
        for it in j:
            if isinstance(it, dict) and url_field in it:
                urls.append(it[url_field])
        return urls
    # 못 찾으면 빈 리스트
    return []


def fetch_snapshot_image(snapshot_url: str, timeout: float = 5.0) -> Optional[np.ndarray]:
    """스냅샷 URL에서 이미지를 가져와 OpenCV BGR numpy 배열로 반환합니다.

    예: CCTV 제공 API가 매번 최신 JPEG을 반환하는 경우
    """
    try:
        r = requests.get(snapshot_url, timeout=timeout)
        r.raise_for_status()
        data = r.content
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2_imdecode(arr)
        return img
    except Exception:
        return None


def cv2_imdecode(arr: np.ndarray):
    # Local import here to avoid hard dependency if only fetching JSON
    import cv2

    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def poll_snapshot_to_stream(snapshot_url: str, fps: float = 1.0):
    """
    단순 폴링 제너레이터: snapshot_url을 주기적으로 호출해 OpenCV 이미지를 yield합니다.
    사용 예: for frame in poll_snapshot_to_stream(url, fps=1.0): process(frame)
    """
    period = 1.0 / max(0.0001, fps)
    while True:
        img = fetch_snapshot_image(snapshot_url)
        if img is not None:
            yield img
        time.sleep(period)
