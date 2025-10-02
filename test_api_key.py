#!/usr/bin/env python3
"""
공공데이터포털 API 키 검증 및 서비스 찾기
"""

import requests
import urllib3
import sys
from pathlib import Path

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api_key_validity():
    """API 키 유효성 테스트"""
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    print("🔍 공공데이터포털 API 키 검증 중...")
    print(f"API 키: {api_key}")
    
    # 가능한 CCTV/교통 관련 API 엔드포인트들
    test_endpoints = [
        # 국토교통부 교통CCTV 정보 서비스
        {
            'name': '국토교통부 교통CCTV정보서비스',
            'url': 'https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo',
            'params': {'serviceKey': api_key, 'numOfRows': 5, 'pageNo': 1}
        },
        # 한국도로공사 CCTV 정보
        {
            'name': '한국도로공사 CCTV정보',
            'url': 'https://apis.data.go.kr/B090041/openapi/service/CctvInfoService/getCctvInfo',
            'params': {'serviceKey': api_key, 'numOfRows': 5, 'pageNo': 1}
        },
        # 서울시 CCTV 정보
        {
            'name': '서울시 CCTV 정보',
            'url': 'https://apis.data.go.kr/1471000/seoul/CctvInfoService/getCctvInfo',
            'params': {'serviceKey': api_key, 'numOfRows': 5, 'pageNo': 1}
        },
        # ITS 교통정보
        {
            'name': 'ITS 교통정보서비스',
            'url': 'https://apis.data.go.kr/1613000/ItsTrafficInfoService/getCctvInfo',
            'params': {'serviceKey': api_key, 'numOfRows': 5, 'pageNo': 1}
        },
        # 경찰청 교통CCTV
        {
            'name': '경찰청 교통CCTV정보',  
            'url': 'https://apis.data.go.kr/1320000/TrafficCctvService/getCctvInfo',
            'params': {'serviceKey': api_key, 'numOfRows': 5, 'pageNo': 1}
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, application/xml, text/plain, */*'
    }
    
    successful_apis = []
    
    for endpoint in test_endpoints:
        print(f"\n🔗 테스트 중: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        
        try:
            response = requests.get(
                endpoint['url'],
                params=endpoint['params'],
                headers=headers,
                timeout=10,
                verify=False
            )
            
            print(f"   상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text[:500]  # 처음 500자만
                print(f"   ✅ 성공! 응답 내용 (일부): {content}")
                successful_apis.append(endpoint)
            else:
                print(f"   ❌ 실패: HTTP {response.status_code}")
                if response.text:
                    error_content = response.text[:200]
                    print(f"   오류 내용: {error_content}")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 연결 오류: {e}")
        except Exception as e:
            print(f"   ❌ 기타 오류: {e}")
    
    print("\n" + "="*60)
    print("📊 테스트 결과:")
    
    if successful_apis:
        print(f"✅ {len(successful_apis)}개의 API가 성공적으로 응답했습니다!")
        for api in successful_apis:
            print(f"   • {api['name']}")
            print(f"     URL: {api['url']}")
    else:
        print("❌ 모든 API 테스트가 실패했습니다.")
        print("\n💡 가능한 원인:")
        print("   1. API 키가 만료되었거나 유효하지 않음")
        print("   2. API 키가 다른 서비스용임")
        print("   3. 공공데이터포털 서버 일시 장애")
        print("   4. 네트워크 연결 문제")
        
        print("\n🔧 해결 방안:")
        print("   1. 공공데이터포털(data.go.kr)에서 API 키 상태 확인")
        print("   2. 승인된 서비스 목록 확인")
        print("   3. 일일 호출 한도 확인")
        print("   4. 시뮬레이션 모드 사용")

if __name__ == "__main__":
    test_api_key_validity()