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
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    # NTIS API 필드명에 맞게 매핑
    cam = {
        'id': (it.get('roadsectionid') or it.get('id') or it.get('cctvId') or 
               it.get('spotId') or ''),
        'name': (it.get('cctvname') or it.get('name') or it.get('title') or 
                 it.get('spotName') or ''),
        'stream_url': (it.get('cctvurl') or it.get('streamUrl') or it.get('url') or 
                      it.get('videoUrl') or ''),
        'coordx': (it.get('coordx') or it.get('longitude') or it.get('x') or ''),
        'coordy': (it.get('coordy') or it.get('latitude') or it.get('y') or ''),
        'cctvtype': (it.get('cctvtype') or it.get('cctvType') or it.get('cctv_type') or ''),
        'cctvformat': it.get('cctvformat', ''),
        'cctvresolution': it.get('cctvresolution', ''),
        'filecreatetime': it.get('filecreatetime', ''),
    }
    
    # URL이 없으면 객체에서 URL 패턴 찾기
    if not cam['stream_url']:
        found = _find_url_in_obj(it)
        if found:
            cam['stream_url'] = found
            
    # 필드 정리 (세미콜론 제거 등)
    for key, value in cam.items():
        if isinstance(value, str):
            cam[key] = value.strip().rstrip(';')
            
    return cam


def get_cctv_list(service_key: Optional[str] = None,
                  minX: float = None, maxX: float = None, minY: float = None, maxY: float = None,
                  type: str = None, cctvType: int = None, getType: str = 'json',
                  endpoint: Optional[str] = None, **kwargs) -> List[Dict]:
    """NTIS에서 CCTV 목록을 가져옵니다.
    
    가이드에 따른 정확한 API 호출 방식을 구현합니다.
    """
    api_key = service_key or os.getenv('NTIS_API_KEY', 'e94df8972e194e489d6abbd7e7bc3469')
    if not api_key:
        raise RuntimeError('NTIS API 키가 설정되어 있지 않습니다.')

    # 가이드 기반 정확한 엔드포인트들 (우선순위 순)
    guide_endpoints = [
        # 1. 가이드에서 제시한 원본 URL
        'https://www.its.go.kr/openapi/cctvInfo',
        # 2. 공공데이터포털 표준 서비스들
        'https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo',
        'http://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo',
        # 3. 경찰청 교통정보서비스
        'https://apis.data.go.kr/1262000/TrafficCctvInfoService/getCctvInfo',
        'http://apis.data.go.kr/1262000/TrafficCctvInfoService/getCctvInfo',
        # 4. 기타 가능한 엔드포인트들
        'https://openapi.its.go.kr/api/cctvInfo',
        'http://openapi.its.go.kr/api/cctvInfo'
    ]
    
    url = endpoint or guide_endpoints[0]
    
    # 가이드에 따른 정확한 파라미터 구성
    if 'www.its.go.kr' in (url or ''):
        # ITS 원본 API 파라미터 (가이드 기준)
        params = {
            'apiKey': api_key,
            'type': type or 'all',        # ex(고속도로), its(국도), all(전체)
            'cctvType': str(cctvType or 1),  # 1(실시간), 2(정지영상), 3(모두)
            'getType': getType or 'json'     # json 또는 xml
        }
    else:
        # 공공데이터포털 표준 파라미터
        params = {
            'serviceKey': api_key,
            'resultType': getType or 'json',
            'numOfRows': kwargs.get('numOfRows', 50),
            'pageNo': kwargs.get('pageNo', 1)
        }
    
    # 좌표 파라미터 추가 (대전 지역 기본값)
    if minX is not None or maxX is not None or minY is not None or maxY is not None:
        params.update({
            'minX': str(minX) if minX is not None else '127.2',
            'maxX': str(maxX) if maxX is not None else '127.5',
            'minY': str(minY) if minY is not None else '36.2',
            'maxY': str(maxY) if maxY is not None else '36.5'
        })
    
    # 추가 파라미터 병합
    params.update({k: v for k, v in kwargs.items() if v is not None})
    
    print(f"[NTIS] 가이드 기반 API 호출")
    print(f"[NTIS] URL: {url}")
    print(f"[NTIS] 파라미터: {json.dumps(params, indent=2, ensure_ascii=False)}")

    # 향상된 요청 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, application/xml, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0'
    }
    
    # 여러 엔드포인트 순차 시도
    last_error = None
    endpoints_to_try = [url] if endpoint else guide_endpoints
    
    for i, try_url in enumerate(endpoints_to_try, 1):
        try:
            print(f"[NTIS] 시도 {i}/{len(endpoints_to_try)}: {try_url}")
            
            # 엔드포인트별 파라미터 조정
            current_params = params.copy()
            if 'www.its.go.kr' not in try_url and 'apiKey' in current_params:
                # 공공데이터포털용으로 파라미터 변환
                current_params['serviceKey'] = current_params.pop('apiKey')
                if 'type' in current_params:
                    current_params.pop('type')  # 공공데이터포털에서는 사용하지 않음
            
            # SSL 검증 우회 및 타임아웃 설정
            resp = requests.get(
                try_url, 
                params=current_params, 
                headers=headers,
                timeout=20,
                verify=False,  # SSL 인증서 검증 우회
                allow_redirects=True
            )
            
            print(f"[NTIS] 응답 상태: {resp.status_code}")
            print(f"[NTIS] 응답 크기: {len(resp.text)} bytes")
            print(f"[NTIS] Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
            
            if resp.status_code == 200:
                print(f"[NTIS] ✅ 성공: {try_url}")
                break
            else:
                print(f"[NTIS] ❌ HTTP 오류 {resp.status_code}")
                # 오류 응답 내용 일부 출력
                error_sample = resp.text[:500] if resp.text else "응답 내용 없음"
                print(f"[NTIS] 오류 내용: {error_sample}...")
                raise requests.exceptions.HTTPError(f"HTTP {resp.status_code}")
                
        except requests.exceptions.HTTPError as e:
            print(f"[NTIS] HTTP 오류: {e}")
            last_error = e
            continue
        except requests.exceptions.SSLError as e:
            print(f"[NTIS] SSL 오류: {e}")
            last_error = e
            continue
        except requests.exceptions.ConnectionError as e:
            print(f"[NTIS] 연결 오류: {e}")
            last_error = e
            continue
        except requests.exceptions.Timeout as e:
            print(f"[NTIS] 타임아웃: {e}")
            last_error = e
            continue
        except Exception as e:
            print(f"[NTIS] 기타 오류: {e}")
            last_error = e
            continue
    else:
        error_msg = f"모든 NTIS 엔드포인트 연결 실패.\n"
        error_msg += f"시도한 엔드포인트: {len(endpoints_to_try)}개\n"
        error_msg += f"마지막 오류: {last_error}\n"
        error_msg += f"해결방안: 1) API 키 승인 상태 확인, 2) 서비스 신청 여부 확인, 3) 시뮬레이션 모드 사용"
        raise RuntimeError(error_msg)

    text = resp.text
    if getType and getType.lower() == 'json':
        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f'응답을 JSON으로 파싱할 수 없습니다: {e}')

        candidates = []
        if isinstance(data, dict):
            # NTIS API 응답 구조 처리
            response = data.get('response', {})
            if response:
                header = response.get('header', {})
                result_code = header.get('resultCode', '')
                result_msg = header.get('resultMsg', '')
                
                print(f"[NTIS] API 응답 코드: {result_code}, 메시지: {result_msg}")
                
                if result_code and result_code != '00':
                    raise RuntimeError(f"NTIS API 오류: {result_msg} (코드: {result_code})")
                
                body = response.get('body', {})
                items = body.get('items', {})
                
                if isinstance(items, dict):
                    item = items.get('item', [])
                    if isinstance(item, list):
                        candidates.append(item)
                    elif isinstance(item, dict):
                        candidates.append([item])
                elif isinstance(items, list):
                    candidates.append(items)
                    
            # 기존 후보들도 확인
            for key1 in ('items', 'data', 'result', 'list'):
                if key1 in data:
                    candidates.append(data[key1])
                    
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
