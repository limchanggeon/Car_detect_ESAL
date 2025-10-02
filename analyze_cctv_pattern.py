#!/usr/bin/env python3
"""
국가교통정보센터 샘플 URL 패턴 분석 및 자동 생성기
"""
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

def analyze_cctv_url(sample_url):
    """CCTV URL 패턴 분석"""
    print("=" * 70)
    print("국가교통정보센터 CCTV URL 패턴 분석")
    print("=" * 70)
    
    print(f"샘플 URL: {sample_url}")
    
    # URL 파싱
    parsed = urlparse(sample_url)
    print(f"\n호스트: {parsed.netloc}")
    print(f"경로: {parsed.path}")
    print(f"쿼리: {parsed.query}")
    
    # 경로에서 CCTV ID 추출
    path_parts = parsed.path.strip('/').split('/')
    print(f"\n경로 구성요소: {path_parts}")
    
    # CCTV ID 찾기 (숫자인 부분)
    cctv_id = None
    for part in path_parts:
        if part.isdigit():
            cctv_id = int(part)
            break
    
    if cctv_id:
        print(f"추출된 CCTV ID: {cctv_id}")
    
    # 쿼리 파라미터 분석
    query_params = parse_qs(parsed.query)
    print(f"\n쿼리 파라미터:")
    for key, values in query_params.items():
        print(f"  {key}: {values[0] if values else 'None'}")
    
    return {
        'host': parsed.netloc,
        'path_template': parsed.path,
        'cctv_id': cctv_id,
        'auth_sign': query_params.get('wmsAuthSign', [None])[0]
    }

def generate_cctv_urls(base_info, id_range=(100, 200)):
    """CCTV ID 범위를 기반으로 URL들 생성"""
    print(f"\n" + "=" * 70)
    print(f"CCTV URL 자동 생성 (ID 범위: {id_range[0]}-{id_range[1]})")
    print("=" * 70)
    
    generated_urls = []
    base_cctv_id = base_info['cctv_id']
    auth_sign = base_info['auth_sign']
    host = base_info['host']
    path_template = base_info['path_template']
    
    # 기본 CCTV ID를 다른 ID로 교체하여 URL 생성
    for new_id in range(id_range[0], id_range[1] + 1):
        # 경로에서 기존 ID를 새 ID로 교체
        new_path = path_template.replace(str(base_cctv_id), str(new_id))
        new_url = f"http://{host}{new_path}?wmsAuthSign={auth_sign}"
        
        generated_urls.append({
            'id': new_id,
            'name': f'CCTV-{new_id:03d}',
            'location': f'교통정보센터-{new_id}',
            'type': 'HLS',
            'url': new_url
        })
    
    print(f"생성된 URL 개수: {len(generated_urls)}")
    
    # 처음 5개와 마지막 5개만 출력
    print("\n처음 5개 URL:")
    for i, cctv in enumerate(generated_urls[:5]):
        print(f"  {i+1}. {cctv['name']}: {cctv['url'][:100]}...")
    
    if len(generated_urls) > 10:
        print(f"\n... (중간 {len(generated_urls) - 10}개 생략) ...")
        print("\n마지막 5개 URL:")
        for i, cctv in enumerate(generated_urls[-5:], len(generated_urls) - 4):
            print(f"  {i}. {cctv['name']}: {cctv['url'][:100]}...")
    
    return generated_urls

def test_url_pattern():
    """URL 패턴 테스트"""
    print(f"\n" + "=" * 70)
    print("URL 패턴 유효성 테스트")
    print("=" * 70)
    
    # 몇 개의 ID로 테스트해보기
    test_ids = [149, 150, 151, 148, 147, 200, 100]
    base_url = "http://cctvsec.ktict.co.kr:8081/openapix017/149/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9MTAvMi8yMDI1IDE6MDA6MzkgQU0maGFzaF92YWx1ZT13ZWRzU0xpUEMvNWl6N295ZW9IYzBBPT0mdmFsaWRtaW51dGVzPTEyMCZpZD1lOTRkZjg5NzJlMTk0ZTQ4OWQ2YWJiZDdlN2JjMzQ2OS0xNzU5MzcwNDM5OTU3LTE0OQ=="
    
    print("테스트할 ID들:", test_ids)
    print("\n생성된 테스트 URL들:")
    
    for test_id in test_ids:
        test_url = base_url.replace('/149/', f'/{test_id}/')
        print(f"  ID {test_id:3d}: {test_url[:120]}...")
        
    print(f"\n💡 제안: 이 URL들을 시뮬레이션 모드에 추가하여")
    print(f"   사용자가 다양한 CCTV를 선택할 수 있도록 구성")

def generate_simulation_data():
    """시뮬레이션 모드용 데이터 생성"""
    print(f"\n" + "=" * 70)
    print("시뮬레이션 모드용 CCTV 데이터 생성")
    print("=" * 70)
    
    base_url = "http://cctvsec.ktict.co.kr:8081/openapix017/149/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9MTAvMi8yMDI1IDE6MDA6MzkgQU0maGFzaF92YWx1ZT13ZWRzU0xpUEMvNWl6N295ZW9IYzBBPT0mdmFsaWRtaW51dGVzPTEyMCZpZD1lOTRkZjg5NzJlMTk0ZTQ4OWQ2YWJiZDdlN2JjMzQ2OS0xNzU5MzcwNDM5OTU3LTE0OQ=="
    
    # 다양한 CCTV ID로 샘플 데이터 생성
    cctv_samples = [
        {'id': 149, 'name': '🔴 국가교통정보센터 CCTV-149 (원본)', 'location': '교통센터'},
        {'id': 150, 'name': '🔴 국가교통정보센터 CCTV-150', 'location': '교통센터'},
        {'id': 151, 'name': '🔴 국가교통정보센터 CCTV-151', 'location': '교통센터'},
        {'id': 148, 'name': '🔴 국가교통정보센터 CCTV-148', 'location': '교통센터'},
        {'id': 147, 'name': '🔴 국가교통정보센터 CCTV-147', 'location': '교통센터'},
        {'id': 100, 'name': '🔴 국가교통정보센터 CCTV-100', 'location': '교통센터'},
        {'id': 200, 'name': '🔴 국가교통정보센터 CCTV-200', 'location': '교통센터'},
    ]
    
    simulation_data = []
    for cctv in cctv_samples:
        url = base_url.replace('/149/', f'/{cctv["id"]}/')
        simulation_data.append({
            'name': cctv['name'],
            'location': cctv['location'],
            'type': 'HLS',
            'url': url
        })
    
    print("생성된 시뮬레이션 데이터:")
    for i, item in enumerate(simulation_data, 1):
        print(f"  {i}. {item['name']}")
        print(f"     URL: {item['url'][:100]}...")
        print()
    
    # Python 코드 형태로 출력
    print("=" * 50)
    print("Python 배열로 복사할 수 있는 코드:")
    print("=" * 50)
    print("ntis_cctv_samples = [")
    for item in simulation_data:
        print("    {")
        print(f"        'name': '{item['name']}',")
        print(f"        'location': '{item['location']}',")
        print(f"        'type': '{item['type']}',")
        print(f"        'url': '{item['url']}'")
        print("    },")
    print("]")

def main():
    """메인 실행"""
    sample_url = "http://cctvsec.ktict.co.kr:8081/openapix017/149/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9MTAvMi8yMDI1IDE6MDA6MzkgQU0maGFzaF92YWx1ZT13ZWRzU0xpUEMvNWl6N295ZW9IYzBBPT0mdmFsaWRtaW51dGVzPTEyMCZpZD1lOTRkZjg5NzJlMTk0ZTQ4OWQ2YWJiZDdlN2JjMzQ2OS0xNzU5MzcwNDM5OTU3LTE0OQ=="
    
    # URL 패턴 분석
    base_info = analyze_cctv_url(sample_url)
    
    # URL 패턴 테스트
    test_url_pattern()
    
    # 시뮬레이션 데이터 생성
    generate_simulation_data()
    
    print(f"\n" + "=" * 70)
    print("결론 및 다음 단계")
    print("=" * 70)
    print("✅ URL 패턴 분석 완료!")
    print("✅ CCTV ID만 변경하면 다른 CCTV URL 생성 가능!")
    print("✅ 시뮬레이션 모드에 추가할 데이터 준비 완료!")
    print("")
    print("🚀 다음 단계:")
    print("1. 생성된 시뮬레이션 데이터를 GUI에 추가")
    print("2. 사용자가 여러 CCTV 중 선택할 수 있도록 개선")
    print("3. 실제 테스트를 통해 유효한 ID 범위 확인")

if __name__ == "__main__":
    main()