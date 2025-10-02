#!/usr/bin/env python3
"""
NTIS API 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_ntis_api():
    """NTIS API 테스트"""
    print("🚨 NTIS API 테스트 시작...")
    
    try:
        from car_detect_esal.api.ntis_client import get_cctv_list
        
        # API 키 (발급받은 키)
        api_key = "e94df8972e194e489d6abbd7e7bc3469"
        
        print(f"📋 API 키: {api_key}")
        print("🔄 CCTV 목록 요청 중...")
        
        # CCTV 목록 요청
        cctv_list = get_cctv_list(
            service_key=api_key,
            numOfRows=10,  # 테스트용으로 10개만
            pageNo=1,
            getType='json'
        )
        
        print(f"✅ {len(cctv_list)}개의 CCTV를 찾았습니다!")
        print("\n" + "="*80)
        
        # 결과 출력
        for i, cctv in enumerate(cctv_list[:5], 1):  # 상위 5개만 출력
            print(f"📹 CCTV #{i}")
            print(f"   ID: {cctv.get('id', 'N/A')}")
            print(f"   이름: {cctv.get('name', 'N/A')}")
            print(f"   위치: ({cctv.get('coordx', 'N/A')}, {cctv.get('coordy', 'N/A')})")
            print(f"   타입: {cctv.get('cctvtype', 'N/A')}")
            print(f"   해상도: {cctv.get('cctvresolution', 'N/A')}")
            
            stream_url = cctv.get('stream_url', '')
            if stream_url:
                if stream_url.startswith(('http', 'rtsp')):
                    print(f"   ✅ 스트림 URL: {stream_url}")
                else:
                    print(f"   ⚠️  스트림 URL: {stream_url} (유효하지 않을 수 있음)")
            else:
                print(f"   ❌ 스트림 URL: 없음")
            
            print("-" * 60)
        
        # 통계
        valid_streams = sum(1 for cctv in cctv_list 
                          if cctv.get('stream_url', '').startswith(('http', 'rtsp')))
        
        print(f"\n📊 통계:")
        print(f"   • 총 CCTV 수: {len(cctv_list)}")
        print(f"   • 유효한 스트림: {valid_streams}")
        print(f"   • 유효 비율: {valid_streams/len(cctv_list)*100:.1f}%" if cctv_list else "0%")
        
        if valid_streams > 0:
            print(f"\n🎉 성공! {valid_streams}개의 실시간 CCTV를 사용할 수 있습니다.")
            
            # 첫 번째 유효한 CCTV 정보 출력
            for cctv in cctv_list:
                if cctv.get('stream_url', '').startswith(('http', 'rtsp')):
                    print(f"\n🔗 테스트용 CCTV:")
                    print(f"   이름: {cctv.get('name', 'Unknown')}")
                    print(f"   URL: {cctv.get('stream_url')}")
                    break
        else:
            print(f"\n⚠️  유효한 스트림 URL이 없습니다.")
            print(f"    API 응답은 정상이지만 실시간 스트림 URL을 제공하지 않을 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        print(f"\n🔧 해결 방법:")
        print(f"   1. 인터넷 연결 확인")
        print(f"   2. API 키 유효성 확인")
        print(f"   3. requests 라이브러리 설치: pip install requests")
        print(f"   4. NTIS API 서버 상태 확인")
        
if __name__ == "__main__":
    test_ntis_api()