# Painter MCP 베이킹·내보내기 테스트 결과

2026-11-05 / Painter 9.0.0 / 512×512 / DirectX normal

테스트 전 프로젝트가 열려 있지 않은 상태를 확인하고 별도 메시와 프로젝트를 생성했다.

- 저해상도 메시: test_low.obj (32×16 구면 격자)
- 고해상도 메시: test_high.obj (128×64 격자, 물결 요철 추가)
- MCP configure_and_bake 호출 성공: 노멀, 월드 노멀, AO, 곡률, 위치, 두께
- 메시 맵 6장 저장 및 이미지 디코딩 확인
- PBR Metallic Roughness 프리셋: PNG 5장
- Unreal Engine 4 (Packed) 프리셋: PNG 3장, UE5용 출력 폴더에 저장
- 전체 14장: 512×512, 유효한 PNG, 파일 크기 및 표본 색상 검사 완료
- MCP save_project 호출 성공 및 MCP_Bake_Export_Test.spp 생성 확인

기본 레이어만 있는 테스트이므로 BaseColor, Roughness, Metallic, Height는 단색이다. 베이킹한 노멀 맵에는 고해상도 메시의 물결 요철이 나타난다. 볼록한 구면이므로 AO는 거의 흰색이다. UE5 에디터로 가져오기 및 머티리얼 연결은 이번 테스트 범위에 포함하지 않았다.

수정한 연결 코드:

1. 한국어/영어 베이킹 매개변수 이름 처리
2. 내보내기 API를 실제 Painter 9 딕셔너리 설정 방식으로 변경
3. 내보내기 성공 상태와 실제 파일 존재 확인
4. Windows 경로가 포함된 프로젝트 저장 코드의 이스케이프 오류 수정
5. Painter API 오류를 MCP 호출 실패로 전달

실행 예시(프로젝트 루트):

```powershell
& Tools/substance-painter-remote-mcp/.venv/Scripts/python.exe Tools/substance-painter-remote-mcp/bake_export_test.py bake
& Tools/substance-painter-remote-mcp/.venv/Scripts/python.exe Tools/substance-painter-remote-mcp/bake_export_test.py export
& Tools/substance-painter-remote-mcp/.venv/Scripts/python.exe Tools/substance-painter-remote-mcp/bake_export_test.py maps
```

이 명령들은 현재 열린 프로젝트를 대상으로 하므로 재실행 전에 MCP_Bake_Export_Test 프로젝트인지 확인한다. create 모드는 프로젝트가 열려 있으면 중단한다.

자세한 파일 검사: image-validation.json
베이킹 응답: bake-result.json
내보내기 응답: PBR-export-result.json, UE5-export-result.json

프리셋 로그 참고: 이 테스트 프로젝트에는 Opacity와 Emissive 채널이 없어 관련 경고가 발생했고 Emissive 출력은 생략됐다. 파일 개수는 실제 생성된 출력 기준이다.

## UE5 머티리얼 연결 검증

- 엔진: Unreal Engine 5.8.4
- 프로젝트: ../../JellyGame.uproject (표시 이름 Jelly Game)
- 테스트 레벨: /Game/JellyGame/Maps/L_PainterMaterialTest
- 에셋 폴더: /Game/JellyGame/Experiments/PainterPipeline
- M_PainterTest: BaseColor RGB→Base Color, Normal RGB→Normal, ORM R→AO / G→Roughness / B→Metallic
- 설정: BaseColor sRGB 켜기, Normal sRGB 끄기+Normalmap, ORM sRGB 끄기+Masks
- 메시 SM_PainterTest의 슬롯 0에 M_PainterTest 할당
- 실제 렌더러에서 텍스처 참조 3개와 연결 5개 확인
- 검증 JSON: ../../Docs/SubstancePainterMCP/ue5-validation.json
- 별도 실습 글: ../../Docs/SubstancePainterMCP/painter-to-ue5.ko.md

UE5에서 실행할 때는 JellyGame.uproject를 열고 L_PainterMaterialTest 레벨을 확인한다. 현재 단계는 PBR 머티리얼 테스트이며 젤리 캐릭터 게임플레이 구현 전이다.
