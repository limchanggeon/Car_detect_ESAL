#!/usr/bin/env python3
"""
공공데이터포털 CCTV 관련 서비스 테스트
정확한 서비스명과 엔드포인트 확인
"""
import requests
import json
from urllib.parse import urlencode

def test_public_data_portal_services():
    """공공데이터포털의 CCTV 관련 서비스들 테스트"""
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 공공데이터포털에서 제공하는 교통/CCTV 관련 서비스들
    services = [
        {
            'name': '국토교통부_교통정보서비스_CCTV정보',
            'endpoint': 'https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        },
        {
            'name': '국토교통부_실시간교통정보서비스_CCTV영상정보',
            'endpoint': 'https://apis.data.go.kr/1613000/RealTimeTrafficInfo/getCctvVideoInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        },
        {
            'name': '경찰청_교통CCTV정보',
            'endpoint': 'https://apis.data.go.kr/1262000/TrafficCctvInfoService/getCctvInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        },
        {
            'name': '한국도로공사_고속도로CCTV정보',
            'endpoint': 'https://apis.data.go.kr/B552061/frequentzoneLiveVideo/getFrequentzoneLiveVideo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        },
        {
            'name': '서울시_교통CCTV정보',
            'endpoint': 'https://apis.data.go.kr/6260000/TrafficCctvInfoService/getCctvInfo',
            'params': {
                'serviceKey': api_key,
                'resultType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        }
    ]
    
    print("공공데이터포털 CCTV 관련 서비스 테스트")
    print("=" * 60)
    
    for i, service in enumerate(services, 1):
        print(f"\n{i}. {service['name']}")
        print(f"   엔드포인트: {service['endpoint']}")
        
        try:
            response = requests.get(
                service['endpoint'], 
                params=service['params'], 
                timeout=10
            )
            
            print(f"   상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 성공! 응답 크기: {len(response.text)} bytes")
                
                try:
                    data = response.json()
                    print(f"   ✅ JSON 파싱 성공")
                    
                    # 응답 구조 분석
                    if isinstance(data, dict):
                        print(f"   응답 구조:")
                        for key in data.keys():
                            if isinstance(data[key], dict):
                                print(f"     {key}: dict (키: {list(data[key].keys())})")
                            elif isinstance(data[key], list):
                                print(f"     {key}: list (길이: {len(data[key])})")
                            else:
                                print(f"     {key}: {type(data[key]).__name__} = {data[key]}")
                        
                        # 에러 코드 확인
                        if 'response' in data:
                            header = data['response'].get('header', {})
                            result_code = header.get('resultCode')
                            result_msg = header.get('resultMsg')
                            if result_code:
                                print(f"   API 결과: {result_code} - {result_msg}")
                        
                        # 데이터 샘플 출력
                        print(f"   응답 샘플 (처음 500자):")
                        print(f"   {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️ JSON 파싱 실패")
                    print(f"   응답 내용: {response.text[:300]}...")
                    
            elif response.status_code == 401:
                print(f"   ❌ 인증 실패 (401) - API 키 확인 필요")
                print(f"   응답: {response.text[:200]}...")
                
            elif response.status_code == 403:
                print(f"   ❌ 접근 거부 (403) - 서비스 승인 필요")
                print(f"   응답: {response.text[:200]}...")
                
            elif response.status_code == 404:
                print(f"   ❌ 서비스를 찾을 수 없음 (404)")
                print(f"   응답: {response.text[:200]}...")
                
            else:
                print(f"   ❌ 기타 오류 ({response.status_code})")
                print(f"   응답: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 연결 실패")
        except requests.exceptions.Timeout:
            print(f"   ❌ 타임아웃")
        except Exception as e:
            print(f"   ❌ 기타 에러: {e}")

def test_api_key_validation():
    """API 키 유효성 검증"""
    print("\n" + "=" * 60)
    print("API 키 유효성 검증")
    print("=" * 60)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 간단한 공공데이터포털 서비스로 키 유효성 테스트
    test_endpoint = "https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo"
    
    params = {
        'serviceKey': api_key,
        'resultType': 'json',
        'numOfRows': '1',
        'pageNo': '1'
    }
    
    print(f"API 키: {api_key}")
    print(f"테스트 엔드포인트: {test_endpoint}")
    
    try:
        response = requests.get(test_endpoint, params=params, timeout=10)
        
        print(f"상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'response' in data:
                    header = data['response'].get('header', {})
                    result_code = header.get('resultCode')
                    result_msg = header.get('resultMsg')
                    
                    if result_code == '00':
                        print("✅ API 키가 유효하고 서비스가 정상 작동합니다!")
                    elif result_code == '01':
                        print("❌ 애플리케이션 에러")
                    elif result_code == '02':
                        print("❌ 데이터베이스 에러")
                    elif result_code == '03':
                        print("❌ 데이터없음 에러")
                    elif result_code == '04':
                        print("❌ HTTP 에러")
                    elif result_code == '05':
                        print("❌ 서비스 연결 실패 에러")
                    elif result_code == '20':
                        print("❌ 서비스 접근 거부 에러")
                    elif result_code == '22':
                        print("❌ 서비스 요청 제한 횟수 초과 에러")
                    elif result_code == '30':
                        print("❌ 등록되지 않은 서비스키")
                    elif result_code == '31':
                        print("❌ 기한 만료된 서비스키")
                    elif result_code == '32':
                        print("❌ 등록되지 않은 IP")
                    elif result_code == '33':
                        print("❌ 서명된 요청이 아님")
                    else:
                        print(f"❌ 알 수 없는 결과 코드: {result_code}")
                    
                    print(f"결과 메시지: {result_msg}")
                    
            except json.JSONDecodeError:
                print("⚠️ JSON 파싱 실패")
                print(f"응답 내용: {response.text[:500]}")
                
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"응답 내용: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ 요청 실패: {e}")

def main():
    """메인 테스트 실행"""
    test_public_data_portal_services()
    test_api_key_validation()
    
    print("\n" + "=" * 60)
    print("결론 및 권장사항")
    print("=" * 60)
    print("1. 대부분의 CCTV API가 404 또는 연결 실패를 반환합니다.")
    print("2. 이는 다음 중 하나의 이유 때문일 수 있습니다:")
    print("   - 서비스 URL이 변경되었거나 서비스가 중단됨")
    print("   - 발급받은 API 키가 해당 서비스에 승인되지 않음")
    print("   - IP 기반 접근 제한이 있음")
    print("3. 권장 해결책:")
    print("   - 공공데이터포털에서 현재 제공되는 CCTV 서비스 목록 재확인")
    print("   - API 키의 승인 서비스 목록 확인")
    print("   - 서비스 제공기관에 문의")

if __name__ == "__main__":
    main()