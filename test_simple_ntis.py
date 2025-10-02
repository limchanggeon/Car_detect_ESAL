#!/usr/bin/env python3
"""
간단한 NTIS API 테스트
"""
import sys
import os

# 프로젝트 경로 추가
sys.path.append('/Users/limchang-geon/Downloads/runs/detect/train2/prog/src')

from car_detect_esal.api.ntis_client import get_cctv_list

def test_simple():
    """간단한 API 테스트"""
    print("간단한 NTIS API 테스트")
    print("=" * 50)
    
    try:
        # 서울 근처 고속도로 CCTV (넓은 범위)
        cctv_list = get_cctv_list(
            service_key="e94df8972e194e489d6abbd7e7bc3469",
            type='ex',           # 고속도로
            cctvType=1,          # 실시간 스트리밍
            minX=127.0,          # 넓은 범위
            maxX=128.0,
            minY=37.0,
            maxY=38.0,
            getType='json',
            endpoint='https://openapi.its.go.kr:9443/cctvInfo'  # 올바른 엔드포인트 직접 지정
        )
        
        print(f"✅ 성공! CCTV 개수: {len(cctv_list)}")
        
        if cctv_list:
            print("\n처음 5개 CCTV:")
            for i, cctv in enumerate(cctv_list[:5], 1):
                print(f"{i}. {cctv.get('name', 'N/A')}")
                print(f"   위치: ({cctv.get('coordx', 'N/A')}, {cctv.get('coordy', 'N/A')})")
                stream_url = cctv.get('stream_url', 'N/A')
                if len(stream_url) > 80:
                    print(f"   스트림: {stream_url[:80]}...")
                else:
                    print(f"   스트림: {stream_url}")
                print(f"   타입: {cctv.get('cctvtype', 'N/A')}, 포맷: {cctv.get('cctvformat', 'N/A')}")
                print()
        
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()