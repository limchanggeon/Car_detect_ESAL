#!/usr/bin/env python3
"""
SSL 검증 우회하여 공공데이터포털 API 테스트
"""
import requests
import urllib3
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_session():
    """SSL 검증을 우회하는 requests 세션 생성"""
    session = requests.Session()
    
    # 재시도 전략 설정
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
    })
    
    return session

def test_working_api_endpoints():
    """실제 작동하는 공공데이터 API 엔드포인트 테스트"""
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    session = create_session()
    
    # 작동 가능성이 높은 서비스들
    services = [
        {
            'name': '국토교통부_교통정보센터_CCTV정보조회서비스',
            'endpoint': 'http://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '5',
                'pageNo': '1'
            }
        },
        {
            'name': '경찰청_교통CCTV정보서비스',
            'endpoint': 'http://apis.data.go.kr/1262000/TrafficCctvInfoService/getCctvInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '5',
                'pageNo': '1'
            }
        },
        {
            'name': '서울특별시_실시간도시데이터API_CCTV',
            'endpoint': 'http://openapi.seoul.go.kr:8088/{}/json/TvcctvInfo/1/5/'.format(api_key),
            'params': {},
            'is_seoul_api': True
        },
        {
            'name': '한국도로공사_고속도로CCTV정보',
            'endpoint': 'http://data.ex.co.kr/openapi/trtm/trafficCctv',
            'params': {
                'key': api_key,
                'type': 'json',
                'numOfRows': '5',
                'pageNo': '1'
            }
        }
    ]
    
    print("실제 작동 가능한 공공데이터 API 엔드포인트 테스트")
    print("=" * 70)
    
    working_apis = []
    
    for i, service in enumerate(services, 1):
        print(f"\n{i}. {service['name']}")
        print(f"   엔드포인트: {service['endpoint']}")
        
        try:
            if service.get('is_seoul_api'):
                # 서울시 API는 URL에 키가 포함됨
                response = session.get(service['endpoint'], timeout=15, verify=False)
            else:
                response = session.get(
                    service['endpoint'], 
                    params=service['params'], 
                    timeout=15, 
                    verify=False
                )
            
            print(f"   상태 코드: {response.status_code}")
            print(f"   응답 크기: {len(response.text)} bytes")
            
            if response.status_code == 200:
                print(f"   ✅ 연결 성공!")
                
                try:
                    data = response.json()
                    print(f"   ✅ JSON 파싱 성공")
                    
                    # 응답 구조 분석
                    if isinstance(data, dict):
                        print(f"   응답 최상위 키: {list(data.keys())}")
                        
                        # 공공데이터포털 표준 응답 구조
                        if 'response' in data:
                            header = data['response'].get('header', {})
                            result_code = header.get('resultCode')
                            result_msg = header.get('resultMsg')
                            
                            print(f"   API 결과: {result_code} - {result_msg}")
                            
                            if result_code == '00':
                                print(f"   🎉 서비스 정상 작동!")
                                working_apis.append(service)
                                
                                # 데이터 확인
                                body = data['response'].get('body', {})
                                items = body.get('items', [])
                                if items:
                                    print(f"   데이터 개수: {len(items)}개")
                                    if isinstance(items, list) and len(items) > 0:
                                        first_item = items[0]
                                        print(f"   첫 번째 데이터 키: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
                                else:
                                    print(f"   ⚠️ 데이터가 없음")
                            else:
                                print(f"   ❌ API 오류: {result_msg}")
                        
                        # 서울시 API 응답 구조
                        elif 'TvcctvInfo' in data:
                            print(f"   서울시 API 응답 확인")
                            result = data['TvcctvInfo']['RESULT']
                            if result['CODE'] == 'INFO-000':
                                print(f"   🎉 서울시 API 정상 작동!")
                                working_apis.append(service)
                            else:
                                print(f"   ❌ 서울시 API 오류: {result['MESSAGE']}")
                        
                        # 기타 응답 구조
                        else:
                            print(f"   ⚠️ 알 수 없는 응답 구조")
                            # 샘플 출력
                            sample = json.dumps(data, ensure_ascii=False, indent=2)[:500]
                            print(f"   응답 샘플: {sample}...")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️ JSON 파싱 실패 - 일반 텍스트 응답")
                    print(f"   응답 샘플: {response.text[:200]}...")
                    
            elif response.status_code == 401:
                print(f"   ❌ 인증 실패 (401) - API 키 문제")
                
            elif response.status_code == 403:
                print(f"   ❌ 접근 거부 (403) - 서비스 승인 필요")
                
            elif response.status_code == 404:
                print(f"   ❌ 서비스를 찾을 수 없음 (404)")
                
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                
            # 에러 응답 내용 출력
            if response.status_code != 200:
                error_content = response.text[:300] if response.text else "응답 내용 없음"
                print(f"   오류 내용: {error_content}...")
                
        except requests.exceptions.SSLError as e:
            print(f"   ❌ SSL 오류: {e}")
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ 연결 오류: {e}")
            
        except requests.exceptions.Timeout:
            print(f"   ❌ 타임아웃")
            
        except Exception as e:
            print(f"   ❌ 기타 오류: {e}")
    
    # 작동하는 API 요약
    print("\n" + "=" * 70)
    print("테스트 결과 요약")
    print("=" * 70)
    
    if working_apis:
        print(f"✅ 작동하는 API 서비스: {len(working_apis)}개")
        for api in working_apis:
            print(f"   - {api['name']}")
            print(f"     {api['endpoint']}")
    else:
        print("❌ 작동하는 API 서비스가 없습니다.")
        
    return working_apis

def test_simple_endpoints():
    """간단한 엔드포인트들 추가 테스트"""
    print("\n" + "=" * 70)
    print("간단한 엔드포인트 추가 테스트")
    print("=" * 70)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    session = create_session()
    
    # 더 간단한 형태의 엔드포인트들
    simple_tests = [
        {
            'name': '공공데이터포털 직접 접근',
            'url': f'https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15013104',
            'method': 'GET'
        },
        {
            'name': 'ITS 포털 메인',
            'url': 'https://www.its.go.kr',
            'method': 'GET'
        },
        {
            'name': '국가교통정보센터 메인',
            'url': 'http://www.its.go.kr',
            'method': 'GET'
        }
    ]
    
    for test in simple_tests:
        print(f"\n테스트: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = session.get(test['url'], timeout=10, verify=False)
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 접속 성공 (응답 크기: {len(response.text)} bytes)")
                
                # HTML 내용에서 API 관련 정보 찾기
                content = response.text.lower()
                if 'api' in content or 'openapi' in content:
                    print("🔍 API 관련 내용 발견됨")
                if 'cctv' in content:
                    print("🔍 CCTV 관련 내용 발견됨")
                    
            else:
                print(f"❌ 접속 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("공공데이터포털 CCTV API 종합 테스트")
    print("API 키: e94df8972e194e489d6abbd7e7bc3469")
    
    # 작동하는 API 찾기
    working_apis = test_working_api_endpoints()
    
    # 간단한 접속 테스트
    test_simple_endpoints()
    
    print("\n" + "=" * 70)
    print("최종 결론")
    print("=" * 70)
    
    if working_apis:
        print("✅ 사용 가능한 API 서비스가 발견되었습니다!")
        print("권장사항:")
        print("1. 발견된 API를 프로젝트에 통합하세요")
        print("2. 각 API의 상세 문서를 확인하여 파라미터를 조정하세요")
        print("3. 데이터 형식에 맞게 파싱 로직을 구현하세요")
    else:
        print("❌ 현재 사용 가능한 API 서비스를 찾지 못했습니다.")
        print("문제 해결 방안:")
        print("1. 공공데이터포털에서 API 키의 승인 상태를 확인하세요")
        print("2. 서비스 신청이 필요한지 확인하세요")
        print("3. IP 제한이 있는지 확인하세요")
        print("4. 대안으로 시뮬레이션 모드를 계속 사용하세요")

if __name__ == "__main__":
    main()