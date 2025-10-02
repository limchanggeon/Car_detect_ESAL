#!/usr/bin/env python3
"""
국가교통정보센터(ITS) CCTV API 연동 테스트
가이드에 따른 단계별 API 테스트 스크립트
"""
import requests
import json
from urllib.parse import urlencode

def test_step1_browser_url():
    """1단계: 브라우저에서 테스트할 URL 생성"""
    print("=" * 60)
    print("1단계: 브라우저 테스트용 URL 생성")
    print("=" * 60)
    
    # API 키
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 대전 지역 좌표 (가이드 기준)
    params = {
        'apiKey': api_key,
        'type': 'all',        # 도로 유형 (전체)
        'cctvType': '1',      # CCTV 유형 (실시간 스트리밍)
        'minX': '127.2',      # 최소 경도
        'maxX': '127.5',      # 최대 경도
        'minY': '36.2',       # 최소 위도
        'maxY': '36.5',       # 최대 위도
        'getType': 'json'     # 데이터 형식 (JSON)
    }
    
    base_url = "https://www.its.go.kr/openapi/cctvInfo"
    full_url = f"{base_url}?{urlencode(params)}"
    
    print(f"Base URL: {base_url}")
    print(f"Parameters: {params}")
    print(f"\n브라우저에서 테스트할 전체 URL:")
    print(f"{full_url}")
    print(f"\n이 URL을 웹 브라우저 주소창에 붙여넣어 테스트해보세요.")
    
    return full_url, params

def test_step2_python_requests(full_url, params):
    """2단계: Python requests로 API 호출"""
    print("\n" + "=" * 60)
    print("2단계: Python requests로 API 호출")
    print("=" * 60)
    
    base_url = "https://www.its.go.kr/openapi/cctvInfo"
    
    try:
        print(f"API 요청 URL: {base_url}")
        print(f"파라미터: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        # API 호출
        response = requests.get(base_url, params=params, timeout=10)
        
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        # HTTP 응답 코드 확인
        response.raise_for_status()
        
        print("✅ API 호출 성공!")
        
        # 응답 내용 출력 (처음 1000자만)
        response_text = response.text
        print(f"\n응답 내용 (처음 1000자):")
        print(response_text[:1000])
        
        if len(response_text) > 1000:
            print(f"... (총 {len(response_text)}자 중 처음 1000자만 표시)")
        
        # JSON 파싱 시도
        try:
            data = response.json()
            print(f"\n✅ JSON 파싱 성공!")
            
            # 데이터 구조 분석
            if isinstance(data, dict):
                print(f"응답 타입: 딕셔너리")
                print(f"최상위 키들: {list(data.keys())}")
                
                # CCTV 데이터 찾기
                cctv_items = []
                
                # 표준 구조 확인
                if 'body' in data and 'items' in data['body']:
                    cctv_items = data['body']['items']
                elif 'data' in data:
                    cctv_items = data['data']
                elif 'items' in data:
                    cctv_items = data['items']
                
                if cctv_items:
                    print(f"✅ CCTV 데이터 발견: {len(cctv_items)}개")
                    
                    # 첫 번째 CCTV 정보 출력
                    if isinstance(cctv_items, list) and len(cctv_items) > 0:
                        first_cctv = cctv_items[0]
                        print(f"\n--- 첫 번째 CCTV 정보 ---")
                        for key, value in first_cctv.items():
                            print(f"{key}: {value}")
                        print("------------------------")
                else:
                    print("⚠️ CCTV 데이터를 찾을 수 없습니다.")
                    print("전체 응답 구조:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 에러: {e}")
            print(f"응답이 JSON 형식이 아닙니다. 내용:")
            print(response_text[:2000])
            
    except requests.exceptions.HTTPError as errh:
        print(f"❌ HTTP 에러: {errh}")
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text[:1000]}")
        
    except requests.exceptions.ConnectionError as errc:
        print(f"❌ 연결 에러: {errc}")
        print("네트워크 연결을 확인하거나 방화벽 설정을 점검해보세요.")
        
    except requests.exceptions.Timeout as errt:
        print(f"❌ 타임아웃 에러: {errt}")
        print("요청 시간이 초과되었습니다. 네트워크 상태를 확인해보세요.")
        
    except requests.exceptions.RequestException as err:
        print(f"❌ 기타 요청 에러: {err}")

def test_alternative_endpoints():
    """3단계: 대안 엔드포인트들 테스트"""
    print("\n" + "=" * 60)
    print("3단계: 대안 엔드포인트들 테스트")
    print("=" * 60)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 대안 엔드포인트들
    alternative_endpoints = [
        # 원본 가이드 URL
        "https://www.its.go.kr/openapi/cctvInfo",
        # 공공데이터포털 기반
        "https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo",
        "http://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo",
        # 국가교통정보센터 직접
        "https://openapi.its.go.kr/api/cctvInfo", 
        "http://openapi.its.go.kr/api/cctvInfo",
        # 기타 가능한 엔드포인트
        "https://data.ex.co.kr/openapi/locationinfo/locationinfoOpenApiCctvList",
    ]
    
    base_params = {
        'minX': '127.2',
        'maxX': '127.5', 
        'minY': '36.2',
        'maxY': '36.5',
        'getType': 'json'
    }
    
    for i, endpoint in enumerate(alternative_endpoints, 1):
        print(f"\n{i}. 테스트 중: {endpoint}")
        
        # 각 엔드포인트에 맞는 파라미터 설정
        if 'data.go.kr' in endpoint:
            # 공공데이터포털용 파라미터
            params = {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '50',
                'pageNo': '1',
                **base_params
            }
        elif 'ex.co.kr' in endpoint:
            # 한국도로공사용 파라미터
            params = {
                'key': api_key,
                'type': 'json',
                **base_params
            }
        else:
            # 기본 ITS 파라미터
            params = {
                'apiKey': api_key,
                'type': 'all',
                'cctvType': '1',
                **base_params
            }
        
        try:
            response = requests.get(endpoint, params=params, timeout=5)
            print(f"   상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 성공! 응답 크기: {len(response.text)} bytes")
                
                # JSON 파싱 시도
                try:
                    data = response.json()
                    print(f"   ✅ JSON 파싱 성공")
                    if isinstance(data, dict):
                        print(f"   키들: {list(data.keys())}")
                except:
                    print(f"   ⚠️ JSON 파싱 실패, 텍스트 응답")
                    print(f"   내용 샘플: {response.text[:200]}...")
            else:
                print(f"   ❌ 실패: {response.status_code}")
                print(f"   에러 내용: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ 타임아웃")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 연결 실패")
        except Exception as e:
            print(f"   ❌ 기타 에러: {e}")

def main():
    """메인 테스트 실행"""
    print("국가교통정보센터(ITS) CCTV API 연동 테스트")
    print("API 키: e94df8972e194e489d6abbd7e7bc3469")
    print("테스트 지역: 대전 (위도 36.2-36.5, 경도 127.2-127.5)")
    
    # 1단계: 브라우저 URL 생성
    full_url, params = test_step1_browser_url()
    
    # 2단계: Python requests 테스트
    test_step2_python_requests(full_url, params)
    
    # 3단계: 대안 엔드포인트들 테스트
    test_alternative_endpoints()
    
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
    print("다음 단계:")
    print("1. 브라우저에서 생성된 URL을 직접 테스트해보세요")
    print("2. 성공한 엔드포인트가 있다면 해당 URL을 사용하세요")
    print("3. 모든 엔드포인트가 실패한다면 API 키 승인 상태를 확인하세요")

if __name__ == "__main__":
    main()