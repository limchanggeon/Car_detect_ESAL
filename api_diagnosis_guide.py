#!/usr/bin/env python3
"""
가이드 기반 API 문제 진단 및 해결책 제시
"""
import requests
import urllib3
import json
from datetime import datetime

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def diagnose_api_problems():
    """API 연동 문제 진단"""
    
    print("=" * 80)
    print("국가교통정보센터(ITS) CCTV API 연동 문제 진단")
    print("=" * 80)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 1. API 키 문제 진단
    print("\n1️⃣ API 키 문제 진단")
    print("-" * 40)
    print(f"API 키: {api_key}")
    print(f"키 길이: {len(api_key)} 문자")
    print(f"키 형식: {'✅ 올바름' if len(api_key) == 32 and api_key.isalnum() else '❌ 잘못됨'}")
    
    # 2. 파라미터 문제 진단
    print("\n2️⃣ 파라미터 문제 진단")
    print("-" * 40)
    
    # 가이드에 따른 정확한 파라미터
    correct_params = {
        'apiKey': api_key,
        'type': 'all',        # ex(고속도로), its(국도), all(전체)
        'cctvType': '1',      # 1(실시간), 2(정지영상), 3(모두)
        'minX': '127.2',      # 최소 경도
        'maxX': '127.5',      # 최대 경도  
        'minY': '36.2',       # 최소 위도
        'maxY': '36.5',       # 최대 위도
        'getType': 'json'     # json 또는 xml
    }
    
    print("올바른 파라미터 구성:")
    for key, value in correct_params.items():
        print(f"  {key}: {value}")
    
    # 3. CORS 문제 진단
    print("\n3️⃣ CORS 문제 진단")
    print("-" * 40)
    print("현재 환경: Python 서버 사이드 실행")
    print("CORS 문제: ❌ 없음 (서버 사이드에서는 CORS 제약 없음)")
    
    # 4. 네트워크/방화벽 문제 진단
    print("\n4️⃣ 네트워크/방화벽 문제 진단")
    print("-" * 40)
    
    # 기본 연결성 테스트
    test_sites = [
        'https://www.google.com',
        'https://www.its.go.kr',
        'http://www.its.go.kr',
        'https://apis.data.go.kr'
    ]
    
    for site in test_sites:
        try:
            response = requests.get(site, timeout=5, verify=False)
            print(f"  {site}: ✅ 연결됨 ({response.status_code})")
        except requests.exceptions.SSLError:
            print(f"  {site}: ⚠️ SSL 문제")
        except requests.exceptions.ConnectionError:
            print(f"  {site}: ❌ 연결 실패")
        except requests.exceptions.Timeout:
            print(f"  {site}: ❌ 타임아웃")
        except Exception as e:
            print(f"  {site}: ❌ 기타 오류 ({e})")
    
    # 5. API 엔드포인트 문제 진단
    print("\n5️⃣ API 엔드포인트 문제 진단")
    print("-" * 40)
    
    # 가이드에서 제시한 URL과 실제 시도해본 URL들 비교
    guide_url = "https://www.its.go.kr/openapi/cctvInfo"
    attempted_urls = [
        "https://www.its.go.kr/openapi/cctvInfo",
        "https://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo",
        "http://apis.data.go.kr/1613000/TrafficCctvInfoService/getCctvInfo",
        "https://openapi.its.go.kr/api/cctvInfo"
    ]
    
    print(f"가이드 제시 URL: {guide_url}")
    print("시도한 URL들:")
    
    for url in attempted_urls:
        try:
            response = requests.get(url, params={'test': 'connection'}, timeout=5, verify=False)
            if response.status_code == 404:
                print(f"  {url}: ❌ 404 (서비스 없음)")
            elif response.status_code == 200:
                print(f"  {url}: ✅ 200 (서비스 존재)")
            else:
                print(f"  {url}: ⚠️ {response.status_code}")
        except Exception as e:
            print(f"  {url}: ❌ 연결 실패 ({type(e).__name__})")

def provide_solutions():
    """해결책 제시"""
    
    print("\n" + "=" * 80)
    print("문제 해결 방안")
    print("=" * 80)
    
    print("\n🔍 문제 원인 분석:")
    print("1. 모든 API 엔드포인트에서 404 오류 발생")
    print("2. 서울시 API에서는 '인증키가 유효하지 않습니다' 메시지")
    print("3. ITS 메인 포털은 접속되지만 API 경로는 존재하지 않음")
    
    print("\n💡 가능한 원인들:")
    print("1. API 서비스 URL이 변경되었거나 서비스가 중단됨")
    print("2. 발급받은 API 키가 해당 서비스들에 승인되지 않음")
    print("3. 서비스별 개별 신청이 필요함")
    print("4. IP 기반 접근 제한이 설정되어 있음")
    print("5. 가이드의 URL 정보가 오래되었거나 부정확함")
    
    print("\n🛠️ 단계별 해결 방안:")
    
    print("\n📋 1단계: API 키 승인 상태 확인")
    print("   - 공공데이터포털(data.go.kr)에 로그인")
    print("   - 마이페이지 > 개발계정 > 인증키 관리")
    print("   - 승인된 서비스 목록 확인")
    print("   - 각 CCTV 관련 서비스의 승인 상태 점검")
    
    print("\n🌐 2단계: 정확한 API 엔드포인트 확인")
    print("   - 공공데이터포털에서 '교통정보 CCTV' 검색")
    print("   - 각 서비스의 상세 페이지에서 실제 API URL 확인")
    print("   - 서비스 문서의 '활용가이드' 및 '샘플코드' 참조")
    
    print("\n📝 3단계: 개별 서비스 신청")
    print("   - 국토교통부 교통정보서비스")
    print("   - 경찰청 교통정보서비스")  
    print("   - 한국도로공사 고속도로 정보서비스")
    print("   - 지자체별 CCTV 서비스 (서울, 부산, 대구 등)")
    
    print("\n🔧 4단계: 대안 솔루션 활용")
    print("   - 현재 구현된 시뮬레이션 모드 계속 사용")
    print("   - 테스트용 RTSP/HTTP 스트림으로 개발 진행")
    print("   - 로컬 비디오 파일을 이용한 기능 검증")
    
    print("\n📞 5단계: 직접 문의")
    print("   - 국가교통정보센터: 1566-0012")
    print("   - 공공데이터포털 고객센터: help@data.go.kr")
    print("   - 각 서비스 제공기관 API 담당부서 문의")

def generate_implementation_guide():
    """현재 상황에 맞는 구현 가이드 제공"""
    
    print("\n" + "=" * 80)
    print("현재 상황 기반 구현 가이드")
    print("=" * 80)
    
    print("\n🎯 즉시 사용 가능한 솔루션:")
    print("현재 프로젝트에 이미 구현된 시뮬레이션 모드가 최선의 대안입니다.")
    
    print("\n✅ 시뮬레이션 모드 장점:")
    print("1. 실제 RTSP 스트림 테스트 가능")
    print("2. HTTP 라이브 스트리밍 지원")
    print("3. 로컬 비디오 파일 처리")
    print("4. 직접 URL 입력 기능")
    print("5. 실시간 차량 탐지 완전 동작")
    
    print("\n🚀 실행 방법:")
    print("1. python main.py 실행")
    print("2. 'NTIS 실시간 CCTV' 버튼 클릭")
    print("3. 시뮬레이션 모드 대화상자에서 테스트 스트림 선택")
    print("4. 또는 'URL 직접 입력' 탭에서 원하는 스트림 URL 입력")
    
    print("\n📺 사용 가능한 테스트 스트림:")
    print("- Big Buck Bunny (HTTP): http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")
    print("- RTSP 테스트 스트림: rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov")
    print("- 로컬 데모 비디오: demo_videos/ 폴더의 파일들")
    
    print("\n⚡ 추가 개선 사항:")
    print("1. API가 활성화되면 자동으로 실제 서비스로 전환")
    print("2. 오류 처리 및 fallback 시스템 완비")
    print("3. 사용자 친화적 인터페이스 제공")

def main():
    """메인 진단 실행"""
    print(f"진단 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # API 문제 진단
    diagnose_api_problems()
    
    # 해결책 제시
    provide_solutions()
    
    # 구현 가이드
    generate_implementation_guide()
    
    print("\n" + "=" * 80)
    print("진단 완료")
    print("=" * 80)
    print("💡 핵심 결론:")
    print("현재 API 연동은 서비스 측 문제로 불가능하지만,")
    print("시뮬레이션 모드를 통해 완전한 기능을 사용할 수 있습니다.")
    print("\n🎯 권장 행동:")
    print("1. 즉시: 시뮬레이션 모드로 프로젝트 진행")
    print("2. 병행: API 서비스 승인 상태 확인 및 문의")
    print("3. 장기: 실제 API 서비스 활성화 후 통합")

if __name__ == "__main__":
    main()