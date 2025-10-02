#!/usr/bin/env python3
"""
실제 NTIS API 테스트 (올바른 엔드포인트 사용)
"""
import sys
import os

# 프로젝트 경로 추가
sys.path.append('/Users/limchang-geon/Downloads/runs/detect/train2/prog/src')

from car_detect_esal.api.ntis_client import get_cctv_list
import json

def test_real_ntis_api():
    """실제 NTIS API 테스트"""
    print("=" * 70)
    print("실제 NTIS API 테스트 (올바른 엔드포인트)")
    print("=" * 70)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # 테스트 파라미터들
    test_cases = [
        {
            'name': '고속도로 CCTV (서울 근처)',
            'params': {
                'service_key': api_key,
                'type': 'ex',          # 고속도로
                'cctvType': 1,         # 실시간 스트리밍
                'minX': 126.8,         # 서울 서쪽
                'maxX': 127.2,         # 서울 동쪽
                'minY': 37.4,          # 서울 남쪽
                'maxY': 37.7,          # 서울 북쪽
                'getType': 'json'
            }
        },
        {
            'name': '국도 CCTV (부산 근처)',
            'params': {
                'service_key': api_key,
                'type': 'its',         # 국도
                'cctvType': 1,         # 실시간 스트리밍
                'minX': 128.9,         # 부산 서쪽
                'maxX': 129.3,         # 부산 동쪽
                'minY': 35.0,          # 부산 남쪽
                'maxY': 35.3,          # 부산 북쪽
                'getType': 'json'
            }
        },
        {
            'name': '전국 고속도로 CCTV (샘플)',
            'params': {
                'service_key': api_key,
                'type': 'ex',          # 고속도로
                'cctvType': 1,         # 실시간 스트리밍
                'minX': 127.100000,    # 가이드 기본값
                'maxX': 128.890000,
                'minY': 34.100000,
                'maxY': 39.100000,
                'getType': 'json'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 50)
        
        try:
            cctv_list = get_cctv_list(**test_case['params'])
            
            print(f"✅ API 호출 성공!")
            print(f"📹 발견된 CCTV 개수: {len(cctv_list)}")
            
            if cctv_list:
                print(f"\n처음 3개 CCTV 정보:")
                for j, cctv in enumerate(cctv_list[:3], 1):
                    print(f"  {j}. {cctv.get('name', 'N/A')}")
                    print(f"     위치: ({cctv.get('coordx', 'N/A')}, {cctv.get('coordy', 'N/A')})")
                    print(f"     스트림: {cctv.get('stream_url', 'N/A')[:100]}...")
                    print(f"     타입: {cctv.get('cctvtype', 'N/A')}")
                    print()
                
                if len(cctv_list) > 3:
                    print(f"  ... 외 {len(cctv_list) - 3}개 더")
            else:
                print("⚠️ 해당 지역에 CCTV가 없습니다.")
                
        except Exception as e:
            print(f"❌ API 호출 실패: {e}")
            import traceback
            traceback.print_exc()

def test_api_parameters():
    """API 파라미터별 테스트"""
    print(f"\n" + "=" * 70)
    print("API 파라미터별 상세 테스트")
    print("=" * 70)
    
    api_key = "e94df8972e194e489d6abbd7e7bc3469"
    
    # cctvType별 테스트
    cctv_types = [
        (1, '실시간 스트리밍'),
        (2, '동영상 파일'),
        (3, '정지 영상')
    ]
    
    print("\n📹 CCTV 타입별 테스트:")
    for cctv_type, desc in cctv_types:
        print(f"\n  {cctv_type}. {desc}")
        try:
            cctv_list = get_cctv_list(
                service_key=api_key,
                type='ex',
                cctvType=cctv_type,
                minX=127.0, maxX=127.1,  # 작은 범위로 테스트
                minY=37.5, maxY=37.6,
                getType='json'
            )
            print(f"     결과: {len(cctv_list)}개 발견")
            
            if cctv_list:
                sample = cctv_list[0]
                print(f"     샘플: {sample.get('name', 'N/A')}")
                if sample.get('stream_url'):
                    print(f"     스트림: {sample['stream_url'][:80]}...")
                    
        except Exception as e:
            print(f"     오류: {e}")
    
    # type별 테스트
    road_types = [
        ('ex', '고속도로'),
        ('its', '국도')
    ]
    
    print(f"\n🛣️ 도로 타입별 테스트:")
    for road_type, desc in road_types:
        print(f"\n  {road_type}. {desc}")
        try:
            cctv_list = get_cctv_list(
                service_key=api_key,
                type=road_type,
                cctvType=1,
                minX=127.0, maxX=127.5,  # 서울 근처
                minY=37.4, maxY=37.7,
                getType='json'
            )
            print(f"     결과: {len(cctv_list)}개 발견")
            
            if cctv_list:
                sample = cctv_list[0]
                print(f"     샘플: {sample.get('name', 'N/A')}")
                    
        except Exception as e:
            print(f"     오류: {e}")

def main():
    """메인 테스트 실행"""
    print("NTIS 실제 API 종합 테스트")
    print("API 키: e94df8972e194e489d6abbd7e7bc3469")
    print("엔드포인트: https://openapi.its.go.kr:9443/cctvInfo")
    
    # 실제 API 테스트
    test_real_ntis_api()
    
    # 파라미터별 상세 테스트
    test_api_parameters()
    
    print(f"\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)
    print("🎯 다음 단계:")
    print("1. 성공한 경우: GUI에 실제 CCTV 목록 통합")
    print("2. 실패한 경우: API 키 승인 상태 확인 또는 시뮬레이션 모드 계속 사용")

if __name__ == "__main__":
    main()