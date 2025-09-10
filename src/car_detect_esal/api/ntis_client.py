"""NTIS(국가 교통정보센터) API 호출 헬퍼

- get_cctv_list: 원격 API 호출 후 카메라 목록 반환
- parse_cctv_text: 로컬에 저장된 JSON/XML 텍스트를 파싱해서 카메라 목록 반환

반환 포맷: [{'id','name','stream_url','coordx','coordy', ...}, ...]

이 모듈은 다양한 응답 구조를 허용하도록 후보 필드를 검사하고,
비정형 문자열 안의 http(s) URL을 찾아 `stream_url`에 채웁니다.
"""
from typing import List, Dict, Optional
import os
import re
import json
import requests

try:
    import xmltodict
except Exception:
    xmltodict = None


def _find_url_in_obj(obj):
    """재귀적으로 객체에서 http(s) URL을 찾아 반환합니다."""
    if obj is None:
        return None
    if isinstance(obj, str):
        m = re.search(r"(https?://\S+)", obj)
        if m:
            return m.group(1).rstrip(';,')
        return None
    if isinstance(obj, dict):
        for v in obj.values():
            res = _find_url_in_obj(v)
            if res:
                return res
        return None
    if isinstance(obj, list):
        for v in obj:
            res = _find_url_in_obj(v)
            if res:
                return res
        return None
    try:
        s = str(obj)
        m = re.search(r"(https?://\S+)", s)
        if m:
            return m.group(1).rstrip(';,')
    except Exception:
        pass
    return None


def _extract_cam_from_item(it: Dict) -> Dict:
    """항목 딕셔너리에서 표준화된 카메라 dict를 추출한다."""
    cam = {
        'id': it.get('id') or it.get('cctvId') or it.get('spotId') or it.get('roadsectionid') or '',
        'name': it.get('name') or it.get('title') or it.get('spotName') or it.get('cctvname') or '',
        'stream_url': it.get('cctvurl') or it.get('streamUrl') or it.get('url') or it.get('videoUrl') or '',
        'coordx': it.get('coordx') or it.get('longitude') or it.get('x') or '',
        'coordy': it.get('coordy') or it.get('latitude') or it.get('y') or '',
        'cctvtype': it.get('cctvtype') or it.get('cctvType') or it.get('cctv_type') or '',
    }
    if not cam['stream_url']:
        found = _find_url_in_obj(it)
        if found:
            cam['stream_url'] = found
    return cam


def get_cctv_list(service_key: Optional[str] = None,
                  minX: float = None, maxX: float = None, minY: float = None, maxY: float = None,
                  type: str = None, cctvType: int = None, getType: str = 'json',
                  endpoint: Optional[str] = None, **kwargs) -> List[Dict]:
    """NTIS에서 CCTV 목록을 가져옵니다.

    기본 엔드포인트는 예시이며 필요시 `endpoint` 인자로 실제 URL을 넘기세요.
    """
    key = service_key or os.getenv('NTIS_API_KEY')
    if not key:
        raise RuntimeError('NTIS API 키가 설정되어 있지 않습니다.')

    url = endpoint or 'https://api.ntis.go.kr/cctv/getCctvList'
    params = {
        'apiKey': key,
        'type': type,
        'cctvType': cctvType,
        'minX': minX,
        'maxX': maxX,
        'minY': minY,
        'maxY': maxY,
        'getType': getType,
    }
    params = {k: v for k, v in params.items() if v is not None}
    params.update(kwargs)

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()

    text = resp.text
    if getType and getType.lower() == 'json':
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError('응답을 JSON으로 파싱할 수 없습니다')

        candidates = []
        if isinstance(data, dict):
            for key1 in ('items', 'data', 'result', 'list'):
                if key1 in data:
                    candidates.append(data[key1])
            r = data.get('response', {}).get('body', {}).get('items')
            if isinstance(r, dict) and 'item' in r:
                candidates.append(r['item'])
            elif isinstance(r, list):
                candidates.append(r)
        if isinstance(data, list):
            candidates.append(data)

        results: List[Dict] = []
        for c in candidates:
            if isinstance(c, list):
                for it in c:
                    if not isinstance(it, dict):
                        continue
                    cam = _extract_cam_from_item(it)
                    results.append(cam)
                if results:
                    return results

        # fallback: top-level dict fields
        if isinstance(data, dict) and any(k in data for k in ('cctvurl', 'coordx', 'coordy')):
            return [{
                'id': data.get('id', ''),
                'name': data.get('name', ''),
                'stream_url': data.get('cctvurl', '') or data.get('streamUrl', ''),
            }]

        return results
    else:
        if not xmltodict:
            raise RuntimeError('XML 파싱을 위해 xmltodict 설치 권장')
        try:
            parsed = xmltodict.parse(text)
        except Exception:
            raise RuntimeError('XML을 파싱할 수 없습니다')

        root = parsed.get('response') if isinstance(parsed, dict) else None
        if not root:
            return []

        data_items = root.get('data')
        if data_items is None:
            return []
        if isinstance(data_items, dict):
            data_items = [data_items]

        results: List[Dict] = []
        for it in data_items:
            if not isinstance(it, dict):
                continue
            def _clean(v):
                if v is None:
                    return ''
                if isinstance(v, str):
                    return v.strip().rstrip(';')
                return str(v)

            cam = {
                'id': _clean(it.get('roadsectionid') or it.get('id')),
                'name': _clean(it.get('cctvname')),
                'stream_url': _clean(it.get('cctvurl')),
                'coordx': _clean(it.get('coordx')),
                'coordy': _clean(it.get('coordy')),
                'cctvtype': _clean(it.get('cctvtype')),
                'cctvformat': _clean(it.get('cctvformat')),
                'cctvresolution': _clean(it.get('cctvresolution')),
                'filecreatetime': _clean(it.get('filecreatetime')),
            }
            if not cam.get('stream_url'):
                found = _find_url_in_obj(it)
                if found:
                    cam['stream_url'] = found
            results.append(cam)

        return results


def parse_cctv_text(text: str, getType: str = 'json') -> List[Dict]:
    """로컬에 저장된 NTIS 응답(JSON 또는 XML)을 파싱하여 카메라 리스트를 반환합니다.

    네트워크가 불가능할 때 브라우저에서 저장한 응답 파일을 파싱하는 데 사용합니다.
    """
    if getType and getType.lower() == 'json':
        try:
            data = json.loads(text)
        except Exception:
            raise RuntimeError('주어진 텍스트를 JSON으로 파싱할 수 없습니다')

        candidates = []
        if isinstance(data, dict):
            for key1 in ('items', 'data', 'result', 'list'):
                if key1 in data:
                    candidates.append(data[key1])
            r = data.get('response', {}).get('body', {}).get('items')
            if isinstance(r, dict) and 'item' in r:
                candidates.append(r['item'])
            elif isinstance(r, list):
                candidates.append(r)
        if isinstance(data, list):
            candidates.append(data)

        results: List[Dict] = []
        for c in candidates:
            if isinstance(c, list):
                for it in c:
                    if not isinstance(it, dict):
                        continue
                    cam = _extract_cam_from_item(it)
                    results.append(cam)
                if results:
                    return results

        if isinstance(data, dict) and any(k in data for k in ('cctvurl', 'coordx', 'coordy')):
            return [{
                'id': data.get('id', ''),
                'name': data.get('name', ''),
                'stream_url': data.get('cctvurl', '') or data.get('streamUrl', ''),
            }]

        return results
    else:
        if not xmltodict:
            raise RuntimeError('XML 파싱을 위해 xmltodict 설치 권장')
        try:
            parsed = xmltodict.parse(text)
        except Exception:
            raise RuntimeError('주어진 텍스트를 XML로 파싱할 수 없습니다')

        root = parsed.get('response') if isinstance(parsed, dict) else None
        if not root:
            return []

        data_items = root.get('data')
        if data_items is None:
            return []
        if isinstance(data_items, dict):
            data_items = [data_items]

        results: List[Dict] = []
        for it in data_items:
            if not isinstance(it, dict):
                continue
            def _clean(v):
                if v is None:
                    return ''
                if isinstance(v, str):
                    return v.strip().rstrip(';')
                return str(v)

            cam = {
                'id': _clean(it.get('roadsectionid') or it.get('id')),
                'name': _clean(it.get('cctvname')),
                'stream_url': _clean(it.get('cctvurl')),
                'coordx': _clean(it.get('coordx')),
                'coordy': _clean(it.get('coordy')),
                'cctvtype': _clean(it.get('cctvtype')),
            }
            if not cam.get('stream_url'):
                found = _find_url_in_obj(it)
                if found:
                    cam['stream_url'] = found
            results.append(cam)

        return results
