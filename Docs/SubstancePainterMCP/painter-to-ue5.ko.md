# Substance Painter 베이킹 → UE5 텍스처 적용 | ORM·노멀맵 설정

**서브스턴스 페인터에서 베이킹한 텍스처를 UE5 머티리얼에 연결하는 순서.**

테스트 환경: **Painter 9.0.0 / Unreal Engine 5.8.4 / Jelly Game / 512×512**

MCP 설치는 [Painter MCP 연결 방법](blog.ko.md)에 따로 정리했다.

## 1. Substance Painter 베이킹 설정

UV가 있는 로우폴리 메시로 프로젝트를 만든다.

| 항목 | 테스트 설정 |
|---|---|
| Normal Map Format | **DirectX** |
| 문서 해상도 | 512 |
| High Definition Meshes | 하이폴리 메시 |
| Output Size | 512×512 |
| Max Frontal / Rear Distance | 각각 0.05 |
| 베이킹 맵 | Normal, World Space Normal, AO, Curvature, Position, Thickness |

**텍스처 세트 설정 → Bake Mesh Maps → Bake** 순서로 실행한다. 투영 거리는 메시 크기와 요철에 맞게 조정한다.

![Painter 베이킹 결과: 하이폴리 요철을 로우폴리에 적용](images/04-bake-export-test.png)

## 2. 텍스처 내보내기: Unreal Engine Packed

**File → Export Textures**에서 설정한다.

- Output Template: **Unreal Engine 4 (Packed)**
- File Type: **PNG / 8bit**
- Size: **512**

이번 테스트에서 생성된 UE용 파일은 3장이다.

| 파일 끝 이름 | 용도 |
|---|---|
| `_BaseColor.png` | 기본 색상 |
| `_Normal.png` | 노멀맵 |
| `_OcclusionRoughnessMetallic.png` | ORM 패킹맵 |

**ORM 채널: R=AO / G=Roughness / B=Metallic.**

프리셋 이름에 UE4가 들어가지만, 이번 UE5 테스트에서도 같은 채널 구성으로 사용했다. Opacity·Emissive가 없는 프로젝트에서는 해당 채널 경고가 나올 수 있다. 이번 테스트도 Emissive 출력은 생략됐다.

## 3. UE5 프로젝트 생성·텍스처 가져오기

**Games → Blank → Blueprint**로 시작한다. 이번 프로젝트의 표시 이름은 **Jelly Game**, 파일 이름은 `JellyGame.uproject`다.

Content Browser에 메시와 텍스처 3장을 가져온다. 텍스처를 열고 다음 설정을 적용한다.

| 텍스처 | sRGB | Compression Settings |
|---|---|---|
| BaseColor | **켜기** | Default |
| Normal | **끄기** | Normalmap |
| ORM | **끄기** | Masks |

이 테스트는 **DirectX 노멀맵**이므로 **Flip Green Channel은 끈 상태**로 사용했다.

## 4. UE5 머티리얼 연결: BaseColor·Normal·ORM

머티리얼 `M_PainterTest`를 만들고 텍스처 3장을 그래프에 넣는다.

| Texture Sample 출력 | Material 입력 |
|---|---|
| BaseColor **RGB** | Base Color |
| Normal **RGB** | Normal |
| ORM **R** | Ambient Occlusion |
| ORM **G** | Roughness |
| ORM **B** | Metallic |

**Apply → Save** 후 메시의 **Material Slot 0**에 할당한다.

![UE5 머티리얼 그래프: BaseColor·DirectX Normal·ORM 연결](images/05-ue5-material-graph.png)

## 5. Jelly Game 적용 결과

테스트 레벨은 `L_PainterMaterialTest`, 메시와 머티리얼은 `JellyGame/Experiments/PainterPipeline`에 저장했다.

**확인 완료: 텍스처 3장 참조, 머티리얼 입력 5개 연결, 메시 슬롯 할당, 프로젝트·레벨 저장.**

기본 레이어만 사용했으므로 BaseColor·Roughness·Metallic은 단색이다. 표면의 물결 요철은 하이폴리에서 베이킹한 노멀맵으로 표현된다. 이번 실습은 **불투명 PBR 머티리얼 연결 테스트**다.

## UE5 텍스처 오류 체크

| 증상 | 먼저 확인 |
|---|---|
| 표면이 지나치게 번들거림 | ORM **G → Roughness**, sRGB 끄기 |
| 금속처럼 보임 | ORM **B → Metallic** 연결 확인 |
| 요철이 반대로 보임 | DirectX/OpenGL 노멀 형식 확인 |
| 샘플러 타입 오류 | Normal=Normal, ORM=Masks 확인 |
| 메시가 기본 회색으로 보임 | 머티리얼 저장·슬롯 할당 확인 |

태그: **서브스턴스페인터, SubstancePainter, 베이킹, 텍스처내보내기, UE5, 언리얼엔진5, 머티리얼, ORM, 노멀맵**

참고: [Epic Games 머티리얼 입력 안내](https://dev.epicgames.com/documentation/en-us/unreal-engine/material-inputs-in-unreal-engine)
