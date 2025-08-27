
로컬/지역 CCTV API를 PoC와 연동하는 방법

1) API 확인
- 많은 한국 지자체에서 카메라 목록이나 스냅샷/스트림 URL을 반환하는 OpenAPI를 제공합니다. 사용하시는 지역의 OpenAPI 문서를 확인하세요(예: 서울 열린데이터 광장, 각 도·시의 공공데이터 포털).

2) 일반적인 응답 형태
- 일부 API는 최상위에 카메라 목록을 리스트로 반환하고, 다른 API는 {"response": {"items": [...]}}처럼 중첩된 구조를 가집니다. `array_path`로 리스트 위치를 지정하고 `url_field`로 URL 필드명을 설정해 추출하세요.

3) 사용 예시
```python
from cctv_api import fetch_camera_list_from_url, fetch_snapshot_image

api_url = "https://example.gov/api/cameras"
urls = fetch_camera_list_from_url(
    api_url,
    params={"key": "MYKEY"},
    array_path=["response","items"],
    url_field="snapshotUrl",
)
for u in urls[:5]:
    img = fetch_snapshot_image(u)
    if img is not None:
        # OpenCV 또는 GUI로 전달
        pass
```

4) `gui_cctv.py`와의 통합
- 스냅샷 기반 카메라의 경우: `fetch_snapshot_image()` 또는 `poll_snapshot_to_stream()`로 프레임을 주기적으로 받아 `StreamPanel` 또는 `StreamWorker`에 전달하도록 코드를 수정하면 됩니다(예: `StreamWorker`가 `VideoCapture` 대신 raw frame을 수신하도록 변경).
- RTSP나 실시간 스트림 URL이 제공되는 경우: 해당 URL을 그대로 `add_stream()`에 전달하면 됩니다.

5) 참고
- 인증, 호출 제한(rate limits), URL 포맷은 API마다 다릅니다. 샘플 API 응답(JSON)을 알려주시면 해당 포맷에 맞춘 추출기(extractor)를 만들어 드리겠습니다.
