#!/usr/bin/env python3
"""
NTIS API 파라미터 문제 해결 테스트
"""
import requests
import json
import urllib3

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_parameter_combinations():
    """다양한 파라미터 조합 테스트"""
    print("=" * 70)
    print("NTIS API 파라미터 조합 테스트")
    print("=" * 70)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    base_url = "https://openapi.its.go.kr:9443/cctvInfo"
    
    # 다양한 파라미터 조합들
    test_cases = [
        {
            'name': '기본 파라미터 (가이드 예시 그대로)',
            'params': {
                'apiKey': api_key,
                'type': 'ex',
                'cctvType': '1',
                'minX': '127.100000',
                'maxX': '128.890000',
                'minY': '34.100000',
                'maxY': '39.100000',
                'getType': 'json'
            }
        },
        {
            'name': '필수 파라미터만',
            'params': {
                'apiKey': api_key,
                'type': 'ex',
                'cctvType': '1',
                'getType': 'json'
            }
        },
        {
            'name': '좌표 없이',
            'params': {
                'apiKey': api_key,
                'type': 'ex',
                'cctvType': '1',
                'getType': 'json'
            }
        },
        {
            'name': 'serviceKey 파라미터 사용',
            'params': {
                'serviceKey': api_key,  # apiKey 대신 serviceKey
                'type': 'ex',
                'cctvType': '1',
                'minX': '127.100000',
                'maxX': '128.890000',
                'minY': '34.100000',
                'maxY': '39.100000',
                'getType': 'json'
            }
        },
        {
            'name': '국도 타입 테스트',
            'params': {
                'apiKey': api_key,
                'type': 'its',  # 국도
                'cctvType': '1',
                'minX': '127.100000',
                'maxX': '128.890000',
                'minY': '34.100000',
                'maxY': '39.100000',
                'getType': 'json'
            }
        },
        {
            'name': '모든 파라미터 포함',
            'params': {
                'apiKey': api_key,
                'serviceKey': api_key,  # 둘 다 시도
                'type': 'ex',
                'cctvType': '1',
                'minX': '127.100000',
                'maxX': '128.890000',
                'minY': '34.100000',
                'maxY': '39.100000',
                'getType': 'json',
                'numOfRows': '10',
                'pageNo': '1'
            }
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9'
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 50)
        print(f"파라미터: {json.dumps(test_case['params'], indent=2, ensure_ascii=False)}")
        
        try:
            response = requests.get(
                base_url,
                params=test_case['params'],
                headers=headers,
                timeout=15,
                verify=False
            )
            
            print(f"상태 코드: {response.status_code}")
            print(f"응답 크기: {len(response.text)} bytes")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            
            if response.status_code == 200:
                print("✅ 성공!")
                try:
                    data = response.json()
                    print("✅ JSON 파싱 성공")
                    
                    # 응답 구조 분석
                    if 'header' in data:
                        header = data['header']
                        result_code = header.get('resultCode')
                        result_msg = header.get('resultMsg')
                        print(f"API 결과: {result_code} - {result_msg}")
                        
                        if result_code == 0:  # 성공
                            body = data.get('body', {})
                            if isinstance(body, dict):
                                items = body.get('items', []) or body.get('item', [])
                                print(f"🎉 CCTV 데이터 발견: {len(items) if isinstance(items, list) else 1}개")
                                
                                if items:
                                    if isinstance(items, list) and len(items) > 0:
                                        first_item = items[0]
                                    else:
                                        first_item = items
                                    
                                    print("첫 번째 CCTV 정보:")
                                    for key, value in first_item.items():
                                        if len(str(value)) > 100:
                                            print(f"  {key}: {str(value)[:100]}...")
                                        else:
                                            print(f"  {key}: {value}")
                            else:
                                print(f"Body 타입: {type(body)}")
                                print(f"Body 내용: {str(body)[:200]}...")
                    else:
                        print("응답 구조:")
                        print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
                        
                except json.JSONDecodeError:
                    print("❌ JSON 파싱 실패")
                    print(f"응답 내용 (처음 500자): {response.text[:500]}...")
                    
            elif response.status_code == 401:
                print("❌ 인증 오류 (401)")
                try:
                    error_data = response.json()
                    if 'header' in error_data:
                        header = error_data['header']
                        print(f"오류 코드: {header.get('resultCode')}")
                        print(f"오류 메시지: {header.get('resultMsg')}")
                except:
                    print(f"오류 내용: {response.text[:200]}...")
                    
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                print(f"응답 내용: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ 요청 실패: {e}")

def test_simple_request():
    """가장 간단한 요청 테스트"""
    print(f"\n" + "=" * 70)
    print("가장 간단한 API 요청 테스트")
    print("=" * 70)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469" 
    
    # 가이드 예시 그대로
    url = f"https://openapi.its.go.kr:9443/cctvInfo?apiKey={api_key}&type=ex&cctvType=1&minX=127.100000&maxX=128.890000&minY=34.100000&maxY=39.100000&getType=json"
    
    print(f"요청 URL:")
    print(f"{url}")
    
    try:
        response = requests.get(url, timeout=15, verify=False)
        print(f"\n상태 코드: {response.status_code}")
        print(f"응답 크기: {len(response.text)} bytes")
        
        if response.status_code == 200:
            print("✅ 성공!")
            data = response.json()
            print("응답 데이터:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
        else:
            print("❌ 실패")
            print(f"응답: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ 오류: {e}")

def main():
    """메인 테스트"""
    print("NTIS API 파라미터 문제 해결 테스트")
    
    # 파라미터 조합 테스트
    test_parameter_combinations()
    
    # 간단한 요청 테스트
    test_simple_request()
    
    print(f"\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)

if __name__ == "__main__":
    main()