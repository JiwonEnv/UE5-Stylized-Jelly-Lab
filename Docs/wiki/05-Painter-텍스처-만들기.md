# 🖌 5. Painter 텍스처 만들기

내 메시에 맞는 **재료 그림 4장**(BaseColor · Normal · Mask · Paint)을 Substance 3D Painter 에서 만드는 순서입니다.

> **왜 필요하나?** 두께·얼룩·기포 그림은 메시의 UV(펼친 전개도)에 맞춰 그려집니다. 다른 메시의 텍스처를 쓰면 위치가 어긋나 얼룩이 엉뚱한 곳에 찍힙니다.

---

## 1. 새 프로젝트

| 항목 | 선택 | 이유 |
|---|---|---|
| 3D 메시 | 내 FBX (프로젝트의 `SourceAssets/Characters/Jelly/` 에 복사해두고 선택) | OneDrive 폴더는 동기화 중 잠기거나 경로가 바뀔 수 있음 |
| 프로젝트 템플릿 | **PBR - Metallic Roughness Alpha-test** | 일반 PBR + 쓰지 않는 Opacity 채널. Alpha-blend 는 뷰포트가 반투명이라 작업이 헷갈림 |
| 문서 해상도 | **2048** | 1024 는 기포·붓 결이 뭉개짐 |
| 고급 → 노멀 맵 형식 | **DirectX** | 언리얼 방식 (OpenGL 이면 굴곡이 반대로 보임) |
| 고급 → 카메라 가져오기 | 끔 | – |
| 메시에 UV 가 없다면 | 자동 언래핑 켬 | 텍스처는 UV 위에 그려짐 |

## 2. 채널 추가

**Texture Set Settings → Channels 옆 `+`**

| 채널 | 이름 | 담는 것 |
|---|---|---|
| Height | – | 굴곡, 흘러내린 자국 |
| User0 | Bubbles | 속 기포 |
| User1 | Smudge | 손자국 얼룩 |
| User2 | Thickness | **두께 (가장 중요)** |
| User4 | BrushStrokes | 붓 결 |
| User5 | PaintDabs | 물감 덩어리 |

> Painter 기본 채널에는 "두께", "기포" 칸이 없어서 빈 칸(User)을 만들어 정보를 담습니다.

## 3. 두께 굽기 (Bake Mesh Maps)

1. Texture Set Settings → **Bake Mesh Maps**
2. 켜기: **Thickness**, Curvature, Ambient Occlusion, Position
3. 하이폴리가 없으면 **Use Low Poly Mesh as High Poly Mesh** ✅
4. Thickness 의 **Max Distance 를 0.3 정도로** 올림 (기본값이면 배처럼 두꺼운 곳이 전부 최대로 뭉개짐)
5. Bake → Mesh maps 의 Thickness 썸네일이 **회색 그라데이션**인지 확인

> 새까맣거나 단색이면 베이크 실패입니다. 테스트 곰에서 실제로 그랬고, 그때는 메시 형태에서 두께를 따로 계산해 넣었습니다 → [문제 해결](06-문제-해결)

## 4. 레이어 쌓기 (아래 → 위)

모두 **Fill Layer**. 표에 적힌 채널만 켜고 나머지는 끕니다.
마스크가 있으면: 레이어 우클릭 → **Add black mask** → 마스크 안에 **Add fill** → Grayscale 칸에 리소스(검색창에 이름).
`Tri-planar` 표시는 마스크 fill 의 Projection 을 **Tri-planar projection** 으로.

| # | 레이어 | 켤 채널 = 값 | 불투명도 | 마스크 | 하는 일 |
|---|---|---|---|---|---|
| 1 | Jelly Base | BaseColor `#FAF7F7`, Roughness 0.04, Height 0, **User0·1·4·5 = 0** | 100 | – | 바탕. User 채널을 0 으로 덮는 게 중요 (새 User 채널 기본값이 흰색) |
| 2 | Color Clouds Cool | BaseColor `#CCC7F2` | 55 | Clouds 2 · Tri-planar | 라벤더 얼룩 |
| 3 | Color Clouds Warm | BaseColor `#FFE0CC` | 45 | Clouds 3 · Tri-planar | 살구 얼룩 |
| 4 | Thickness | User2 = 베이크한 Thickness 맵 | 100 | – | 두께를 User2 에 복사 ※1 |
| 5 | Cavity Density | BaseColor `#B8ADB8` | 60 | Curvature 맵 + **Levels (Invert, 입력 0.5~0.67)** ※2 | 홈 부분 진하게 |
| 6 | Soft Lumps | Height 0.35 | 35 | 3D Perlin Noise Fractal | 살짝 울퉁불퉁 |
| 7 | Drips | Height 0.6, Roughness 0.02 | 80 | Grunge Rusty Leaks · Tri-planar + Position 제너레이터(Multiply) | 위에서 흘러내린 자국 |
| 8 | Micro Ripples | Height 0.15 | 25 | Liquid · Tri-planar | 잔물결 |
| 9 | Smudges | Roughness 0.22, User1 1 | 100 (마스크 fill 45) | Grunge Wipe Smudgy Heavy · Tri-planar | 손자국 |
| 10 | Bubbles | User0 1, BaseColor 흰색(BaseColor만 25) | 100 | Gaussian Spots 1 · Tri-planar | 속 기포 |
| 11 | Brush Strokes | User4 1 | 100 | Grunge Wipe Brushed Large · Tri-planar | 붓 결 (그림체용) |
| 12 | Paint Dabs | User5 1 | 100 | Grunge Plaster Painted · Tri-planar | 물감 덩어리 (그림체용) |

- **※1** User2 소스 칸 → 리소스 검색 `thickness` → 베이크된 맵. 안 보이면 User2 = 1 + black mask + **Mask Editor** 제너레이터에서 Thickness 가중치만 올리기
- **※2** Curvature 맵은 **회색(0.5)이 평평**, 밝으면 볼록, 어두우면 오목입니다. 그대로 넣으면 전체가 50% 로 칠해지므로 Levels 로 "오목한 곳만 흰색" 으로 바꿉니다.
- **Tri-planar 를 쓰는 이유**: 자동 UV 는 조각이 많아 이음새가 보입니다. Tri-planar 는 3D 공간 기준으로 깔아 이음새가 없고, 흘러내림이 항상 아래로 향합니다.
- 사실적인 젤리만 쓸 거면 11·12 번은 생략해도 됩니다.

## 5. 내보내기

**File → Export Textures → Output Templates** 에서 새 템플릿:

| 파일 | R | G | B | A |
|---|---|---|---|---|
| `이름_BaseColor` | BaseColor R | G | B | – |
| `이름_Normal` | Converted maps → **Normal DirectX** RGB | | | – |
| `이름_Mask` | **User2 (두께)** | 비움 | User0 (기포) | User1 (얼룩) |
| `이름_Paint` | User4 (붓 결) | User5 (물감) | – | – |

PNG · 8bit · Padding **Infinite** · 2048 · 출력 `SourceAssets/Characters/Jelly/Textures`

> **채널 순서가 중요합니다.** 머티리얼이 "Mask 의 R = 두께, B = 기포, A = 얼룩" 으로 읽습니다.

다음: 언리얼에 넣기 → [🚀 바로 써보기 2단계](02-바로-써보기#2-텍스처-가져오기)
