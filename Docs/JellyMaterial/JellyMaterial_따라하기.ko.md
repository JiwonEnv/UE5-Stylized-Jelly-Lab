# 젤리 머티리얼 — 처음부터 따라하기 (쉬운 버전)

> 기존 [JellyMaterialGuide.ko.md](JellyMaterialGuide.ko.md) 는 "만들어진 것의 설명서"(수식·노드 전부)입니다.
> 이 문서는 **내 메시(예: `Gummy.fbx`)에 젤리를 입히려면 무엇을 어떤 순서로 누르면 되는지**, 그리고 **왜 그렇게 하는지**만 정리했습니다.
> 언리얼 머티리얼 그래프는 이미 완성돼 있으니 **직접 노드를 만들 필요는 없습니다.**

---

## 0. 한눈에 보기

```
[Painter]  내 메시 → 두께 베이크 → 레이어 12개 → 텍스처 4장 내보내기
                                                 │
[Unreal]   텍스처 4장 가져오기 → 머티리얼 인스턴스 하나 만들기 → 텍스처 4장 꽂기 → 색 고르기 → 끝
```

| 하는 곳 | 하는 일 | 걸리는 시간 |
|---|---|---|
| Painter | "젤리의 재료 정보"를 그림 (두께, 얼룩, 기포, 붓 결) | 30분~1시간 |
| Unreal | 그 정보를 받아 "젤리처럼 보이게" 계산 (색, 투명, 빛) | 10분 |

---

## 1. 먼저 알아둘 것 — 왜 이렇게 나눴나

### ① 색은 Painter 가 아니라 언리얼에서 정한다
- Painter 에서는 **거의 흰색**으로 칠합니다. 빨강·파랑 같은 실제 색은 언리얼 인스턴스의 `Jelly Color` 한 칸으로 바꿉니다.
- **왜?** 텍스처 한 벌로 젤리 색을 무한히 만들 수 있고, 색을 바꿀 때마다 Painter 로 돌아갈 필요가 없습니다.

### ② 젤리처럼 보이는 핵심은 "두께"
- 진짜 젤리는 **얇은 곳(귀·발끝)은 밝고 투명**하고, **두꺼운 곳(배)은 진하고 탁합니다.** (빛이 젤리를 오래 통과할수록 색을 더 먹기 때문)
- 그래서 Painter 에서 **메시의 두께를 구워서(Thickness 베이크)** 텍스처 한 칸에 담아 언리얼로 넘깁니다. 언리얼은 이 값으로 색 진하기와 투명도를 정합니다.
- **왜 처음 GPT 결과가 밋밋했나?** 두께 정보 없이 한 가지 색 + 투명도만 줬기 때문입니다. 그러면 플라스틱 공처럼 보입니다.

### ③ 언리얼은 "Thin Translucent" 를 쓴다
- 보통의 반투명(Translucent)은 젤리 뒤의 배경을 **색 없이 그대로** 비춥니다 → 뿌옇고 창백해집니다.
- Thin Translucent 는 **뒤 배경을 젤리 색으로 물들여** 비춥니다 → 진짜 젤리처럼 보입니다.
- 이건 마스터 머티리얼 `M_Jelly_Gummy` 에 이미 설정돼 있어서, 인스턴스만 만들면 자동으로 적용됩니다.

### ④ 그림체는 "붓 자국 텍스처 + 화면 필터" 두 단계
- 붓 자국 텍스처로 명암을 **붓 자국 모양 조각**으로 끊고(머티리얼),
- 화면에서 그 젤리만 골라 **유화 필터(Kuwahara)** 를 한 번 더 겁니다(포스트 프로세스).
- **왜 둘 다?** 텍스처만 쓰면 "무늬"처럼 보이고, 필터만 쓰면 "흐릿한 사진"처럼 보입니다. 둘을 겹쳐야 손으로 칠한 느낌이 납니다.

---

## 2. Substance Painter — 따라하기

### STEP 1. 새 프로젝트

| 항목 | 선택 | 왜 |
|---|---|---|
| 3D 메시 | 내 FBX (프로젝트의 `SourceAssets/Characters/Jelly/` 에 복사해두고 선택) | OneDrive 폴더는 동기화 중 잠기거나 경로가 바뀔 수 있음 |
| 프로젝트 템플릿 | **PBR - Metallic Roughness Alpha-test** | 일반 PBR + Opacity 채널. Opacity 는 안 씀(투명은 언리얼이 계산). Alpha-blend 는 뷰포트가 반투명이라 작업이 헷갈림 |
| 문서 해상도 | **2048** | 1024 는 기포·붓 결이 뭉개짐 |
| 고급 설정 → 노멀 맵 형식 | **DirectX** | 언리얼이 DirectX 방식. OpenGL 이면 굴곡이 반대로 보임 |
| 고급 설정 → 카메라 가져오기 | 끔 | 필요 없음 |
| 메시에 UV 가 없다면 | 자동 언래핑 켬 | 텍스처는 UV 위에 그려지므로 UV 가 꼭 필요 |

### STEP 2. 채널 추가
오른쪽 **Texture Set Settings → Channels 옆 `+`** 로 아래를 추가합니다.

| 추가할 채널 | 이름 | 담는 것 | 언리얼에서 쓰는 곳 |
|---|---|---|---|
| Height | – | 굴곡, 흘러내린 자국 | 노멀(표면 굴곡) |
| User0 | Bubbles | 속의 기포 | 밝은 점 |
| User1 | Smudge | 손자국 얼룩 | 살짝 거친 반사 |
| User2 | Thickness | **두께 (가장 중요)** | 색 진하기·투명도 |
| User4 | BrushStrokes | 붓 결 | 그림체 명암 끊기 |
| User5 | PaintDabs | 물감 덩어리 | 그림체 명암 끊기 |

> **왜 User 채널?** Painter 의 기본 채널(BaseColor, Roughness…)에는 "두께", "기포" 같은 칸이 없어서, 빈 칸(User)을 만들어 정보를 담고 나중에 텍스처 한 장에 모아 내보냅니다.

### STEP 3. 두께 굽기 (Bake Mesh Maps)
1. Texture Set Settings → **Bake Mesh Maps**
2. 켜기: **Thickness**, Curvature, Ambient Occlusion, Position
3. 하이폴리가 따로 없으면 **Use Low Poly Mesh as High Poly Mesh** 체크
4. Thickness 설정의 **Max Distance 를 0.3 정도로** 올림
5. Bake

**확인:** Texture Set Settings 의 Mesh maps 에서 Thickness 썸네일이 **회색 그라데이션**이어야 합니다 (얇은 곳 어둡고 두꺼운 곳 밝게).
- 새까맣거나 단색이면 → 베이크 실패. (테스트 곰에서 실제로 이랬습니다.) 저에게 메시를 알려주시면 두께 맵을 따로 계산해 드립니다.

> **왜 Max Distance 를 올리나?** 기본값은 얇은 부분만 구분하고 배처럼 두꺼운 곳은 전부 "최대"로 뭉개져, 몸통 안의 색 변화가 사라집니다.

### STEP 4. 레이어 쌓기
레이어 패널에서 **Fill Layer 추가**를 반복합니다. 아래 표의 **1번이 맨 아래**입니다.

공통 방법:
- 레이어 속성에서 **표에 적힌 채널만 켜고** 나머지 채널 버튼은 끕니다. (안 끄면 아래 레이어 값을 덮어씀)
- "마스크" 칸이 있으면: 레이어 우클릭 → **Add black mask** → 마스크 안에 **Add fill** → 그 fill 의 Grayscale 에 리소스(검색창에 이름 입력)를 넣습니다.
- "Tri-planar" 라고 적혀 있으면 그 마스크 fill 의 Projection 을 **Tri-planar projection** 으로 바꿉니다.

| # | 레이어 | 켤 채널 = 값 | 레이어 불투명도 | 마스크 리소스 | 이 레이어가 하는 일 |
|---|---|---|---|---|---|
| 1 | Jelly Base | BaseColor `#FAF7F7`, Roughness 0.04, Height 0, User0 0, User1 0, User4 0, User5 0 | 100 | – | 바탕. **User 채널을 0으로 덮는 게 중요** (새 User 채널은 기본이 흰색이라 안 덮으면 전부 1로 나감) |
| 2 | Color Clouds Cool | BaseColor `#CCC7F2` | 55 | Clouds 2 · Tri-planar | 은은한 라벤더 얼룩 (레퍼런스의 보랏빛 기운) |
| 3 | Color Clouds Warm | BaseColor `#FFE0CC` | 45 | Clouds 3 · Tri-planar | 은은한 살구 얼룩 |
| 4 | Thickness | User2 = **베이크한 Thickness 맵** (User2 소스 칸 클릭 → 리소스 검색에 `thickness` → 베이크된 맵 선택)* | 100 | – | 두께를 User2 칸에 복사 |
| 5 | Cavity Density | BaseColor `#B8ADB8` | 60 | 베이크한 Curvature 맵 + 그 위에 **Levels (Invert, 입력 0.5~0.67)** ※ | 홈 부분이 진해 보이게 |
| 6 | Soft Lumps | Height 0.35 | 35 | 3D Perlin Noise Fractal | 손으로 만든 듯한 살짝 울퉁불퉁 |
| 7 | Drips | Height 0.6, Roughness 0.02 | 80 | Grunge Rusty Leaks · Tri-planar + 그 위에 Position 제너레이터(Multiply) | 위에서 흘러내린 자국 |
| 8 | Micro Ripples | Height 0.15 | 25 | Liquid · Tri-planar | 아주 잔잔한 물결 |
| 9 | Smudges | Roughness 0.22, User1 1 | 100 (마스크 fill 45) | Grunge Wipe Smudgy Heavy · Tri-planar | 손자국 얼룩 |
| 10 | Bubbles | User0 1, BaseColor 흰색(BaseColor만 25) | 100 | Gaussian Spots 1 · Tri-planar | 속 기포 |
| 11 | Brush Strokes | User4 1 | 100 | Grunge Wipe Brushed Large · Tri-planar | 붓 결 (그림체용) |
| 12 | Paint Dabs | User5 1 | 100 | Grunge Plaster Painted · Tri-planar | 물감 덩어리 (그림체용) |

> \* 리소스 창에 베이크된 Thickness 가 안 보이면: User2 = 1 로 두고 **black mask → Add generator → Mask Editor** 를 넣은 뒤, Mask Editor 에서 Thickness 가중치만 올리고 나머지(Curvature/AO 등)는 0 으로 하면 같은 결과가 됩니다.
>
> ※ Curvature 맵은 **회색(0.5)이 평평, 밝으면 볼록, 어두우면 오목**인 맵이라 그대로 넣으면 전체가 회색 = 마스크가 50% 로 다 칠해집니다.
> 마스크 안 fill 위에 **Add levels** → **Invert** 체크 → 입력 범위 **0.5 ~ 0.67** 로 두면 "오목한 곳만 흰색, 나머지 검정" 이 됩니다.
> (테스트 곰의 `GummyBear_Cavity.png` 는 이 계산 `(0.5 − curvature) × 3` 을 미리 해 둔 맵입니다.)
>
> **왜 Tri-planar?** 자동 언래핑된 메시는 UV 조각이 많아서, 보통 방식으로 노이즈를 깔면 조각 경계에 이음새가 보입니다. Tri-planar 는 UV 대신 3D 공간 기준으로 깔아서 이음새가 없고, 흘러내린 자국도 항상 아래로 향합니다.
>
> **왜 Height 를 약하게?** 젤리는 매끈해야 하이라이트가 또렷합니다. 굴곡이 세면 표면이 모래처럼 보입니다.
>
> **사실적인 젤리만 원하면** 11, 12번은 생략해도 됩니다.

### STEP 5. 내보내기
1. **File → Export Textures**
2. **Output Templates** 탭 → 새 템플릿 만들기 → 아래 4개 맵을 만들고 채널을 끌어다 넣습니다.

| 파일 이름 | R | G | B | A | 왜 이렇게 묶나 |
|---|---|---|---|---|---|
| `이름_BaseColor` | BaseColor RGB | | | | 색 얼룩 (거의 흰색) |
| `이름_Normal` | Converted maps → **Normal DirectX** RGB | | | | Height + 노멀을 합친 굴곡 |
| `이름_Mask` | **User2 (두께)** | 비움 | User0 (기포) | User1 (얼룩) | 흑백 정보 4개를 한 장에 → 텍스처 수 절약 |
| `이름_Paint` | User4 (붓 결) | User5 (물감) | 비움 | | 그림체용 |

3. 설정: PNG, 8bit, Padding = **Infinite**, Size 2048
4. 출력 폴더: `SourceAssets/Characters/Jelly/Textures`

> **순서가 중요합니다.** 언리얼 머티리얼이 "Mask 의 R = 두께, B = 기포, A = 얼룩" 으로 읽게 만들어져 있어서, 자리가 바뀌면 엉뚱하게 보입니다.

---

## 3. Unreal — 따라하기

마스터 머티리얼과 그림체 필터는 이미 있습니다:
- `/Game/JellyGame/Art/Materials/Jelly/M_Jelly_Gummy` — 젤리 계산 전부
- `/Game/JellyGame/Art/Materials/Jelly/Instances/MI_Jelly_*` — 완성된 프리셋들 (복사해서 쓰면 편함)
- `/Game/JellyGame/Art/Materials/PostProcess/M_PP_JellyPaintFilter` — 그림체 화면 필터
- `/Game/JellyGame/Art/Materials/LookDev/M_LookDev_Floor` — 룩데브 바닥
- `/Game/JellyGame/Art/Characters/Jelly/SM_GummyBear` — 테스트 곰 메시 (내 메시도 이 폴더에 두면 정리가 쉬움)

### STEP 1. 메시 가져오기
1. Content Browser 에 FBX 드래그
2. 메시를 열고 Details 에서 **Nanite 끄기 (Enable Nanite Support 체크 해제)** → Apply Changes

> **왜?** 반투명 머티리얼은 Nanite 메시를 아주 거친 대체 메시(약 3천 삼각형)로 그립니다. 켜 두면 젤리가 각져 보입니다.

### STEP 2. 텍스처 가져오기
4장을 `Art/Textures/Jelly` 로, 메시는 `Art/Characters/Jelly` 로 드래그한 뒤, 각각 열어서:

| 텍스처 | sRGB | Compression Settings | 왜 |
|---|---|---|---|
| BaseColor | 켬 | Default | 눈에 보이는 색 |
| Normal | 끔 | **Normalmap** | 방향 데이터 |
| Mask | **끔** | **Masks** | 색이 아니라 숫자 데이터. sRGB 가 켜지면 두께값이 왜곡됨 |
| Paint | **끔** | **Masks** | 위와 같음 |

### STEP 3. 머티리얼 인스턴스 만들기
가장 쉬운 방법: **원하는 느낌의 프리셋을 복사**합니다.

| 원하는 느낌 | 복사할 프리셋 |
|---|---|
| 사실적인 젤리 | `MI_Jelly_Raspberry` (빨강) / `MI_Jelly_Blue` |
| 핑크·보라·블루 섞인 빛 | `MI_Jelly_PinkIridescent` |
| 손그림 파스텔 | `MI_Jelly_PinkPainted` |
| 손그림 + 6각 별 | `MI_Jelly_AmberPainted` |
| 손그림 + 여러 색 빛 + 별 | `MI_Jelly_RedPainted` |
| 손그림 + 여러 색 빛 + **젤리 속 글리터** (최신) | `MI_Jelly_RedPainted_InnerGlitter_TexParam` |

> `MI_Jelly_RedPainted_InnerGlitter_Restored` 는 텍스처가 머티리얼 안에 고정돼 있어 인스턴스에서 못 바꿉니다.
> 같은 룩에 텍스처 칸만 연 복사본이 `…_TexParam` 입니다 (부모 `M_Jelly_Gummy_RedPainted_InnerGlitter_TexParam`). 내 메시에 쓸 땐 이쪽을 복사하세요.
> 이 버전은 텍스처 칸이 5개: 아래 4칸 + `Brush Strokes`(붓 자국 타일, 보통 그대로 둠). 별 텍스처는 글리터 함수 안에 고정입니다.

1. 프리셋 우클릭 → **Duplicate** → 이름 바꾸기 (예: `MI_Gummy_MyRed`)
2. 열어서 **Textures** 그룹의 4칸을 내 텍스처로 교체:
   `BaseColor Tint` ← BaseColor, `Normal` ← Normal, `Mask` ← Mask, `Paint Mask` ← Paint
3. 메시에 이 인스턴스를 드래그

> **왜 복사?** 프리셋마다 수십 개 값이 맞춰져 있어서, 빈 인스턴스에서 시작하면 다시 맞추기 어렵습니다.
>
> ⚠️ `Tools/BuildJellyLookDev.py` 를 다시 실행하면 프리셋 `MI_Jelly_*` 값이 스크립트 값으로 초기화됩니다. 내가 만든 인스턴스는 **다른 이름으로 복사해서** 쓰세요.

### STEP 4. 내 메시 크기에 맞추기
테스트 곰은 높이 44cm 기준입니다. 내 메시 크기가 다르면 아래만 맞추세요.

| 파라미터 (그룹) | 뜻 | 맞추는 법 |
|---|---|---|
| `Object Height` (Color Gradient) | 위→아래 색 그라데이션 기준 높이 | 내 메시 높이(cm) |
| `Brush Scale` (Brush Strokes) | 붓 자국 크기 | 메시 높이 × 1 정도 (곰 44cm → 42) |
| `Star Size` (Sparkle / Edge) | 별 크기 | 메시가 크면 키움 |

### STEP 5. (그림체 프리셋일 때만) 화면 필터 연결
1. 레벨에 **Post Process Volume** 이 있고, Infinite Extent 가 켜져 있으며, Post Process Materials 에 `M_PP_JellyPaintFilter` 가 들어 있는지 확인 (`L_JellyLookDev` 에는 이미 있음)
2. 젤리 액터 선택 → Details 검색창에 `custom depth` →
   **Render CustomDepth Pass 켬**, **CustomDepth Stencil Value = 1**
3. (프로젝트에 한 번만, 이미 설정됨) Project Settings → Rendering → **Custom Depth-Stencil Pass = Enabled with Stencil**

> **왜 스텐실?** 유화 필터는 화면 전체에 걸리는 효과라서, "스텐실 1 이라고 표시한 물체"에만 걸리게 해야 배경·다른 물체가 뭉개지지 않습니다.

---

## 4. 느낌 조절 — 어떤 손잡이를 돌리나

| 하고 싶은 것 | 돌릴 파라미터 | 방향 |
|---|---|---|
| 색 바꾸기 | `Jelly Color` + `Deep Color` | Deep 은 Jelly 를 어둡고 진하게 한 색 |
| 더 진하게 / 더 연하게 | `Density` | 올리면 진함 |
| 더 투명하게 | `Opacity Thin` / `Opacity Thick` | 내리면 투명 |
| 뒤 배경이 더 / 덜 비치게 | `Transmission Brightness` | **0.4 아래로 내리면 회색빛으로 칙칙해짐** |
| 속에서 빛나는 느낌 | `Inner Glow` | 올림 |
| 하이라이트 세기 | `Highlight Intensity` | 올림 |
| 표면 굴곡 줄이기 | `Normal Strength` | 내림 (그림체는 0.05~0.1) |
| 위아래 다른 색 | `Gradient Amount` + Mid/Bottom Color | 주색이 사라지면 0.3~0.4 로 낮춤 |
| 가장자리에 색 빛 | `Rim Light A/B` + `Rim Color A/B` | `Rim Power` 2.5 이상 (낮으면 몸통까지 번져 탁해짐) |
| 무지개빛 | `Iridescence` | 0.1~0.3 |
| 그림체 켜기 | `Paint Style` 1, `Cel Amount` 1, `Brush Amount` 1 | + STEP 5 필터 |
| 붓 자국 크게 | `Brush Scale` | 올림 |
| 별 반짝이 | `Star Glint` 2~3, `Star Points` 4 또는 6 | `Star Zone` 낮추면 더 넓게 퍼짐 |
| 유리 같은 흰 테두리 | `Edge Line` | 0.3~0.8 |
| 그림 필터 세기 | `M_PP_JellyPaintFilter` 의 `Brush Radius` | 4 권장 (6 이상이면 눈·코까지 뭉개짐) |

---

## 5. 이상할 때

| 보이는 증상 | 원인 | 해결 |
|---|---|---|
| 젤리가 회색 체크무늬 | 머티리얼 컴파일 중이거나 실패 | 잠시 기다림. 계속이면 Output Log 확인 |
| 각져 보임 | Nanite 켜져 있음 | 3-STEP 1 |
| 표면이 모래처럼 거침 | Normal 이 너무 셈 / Painter 의 빈 Normal 베이크가 섞임 | `Normal Strength` 내림, Painter Mesh maps 의 빈 Normal 슬롯 비우고 다시 내보내기 |
| 색이 전혀 안 진해짐 (어디나 같은 색) | Mask R(두께)이 비었음 | Painter Thickness 베이크 확인, Mask 텍스처 sRGB 끔 확인 |
| 전부 흰 점투성이 | User0(기포)이 전부 1 | Painter 1번 레이어에서 User0 = 0 |
| 그림체 필터가 안 걸림 | 스텐실 미설정 | 3-STEP 5 |
| 창백하고 뿌옇다 | 흰 바닥이 비침 | 배경을 어둡게 하거나 `Transmission Brightness`·`Opacity` 조절 |

---

## 6. 왜 이런 방법을 골랐나 (요약)

| 선택 | 다른 방법 | 이걸 고른 이유 |
|---|---|---|
| 색은 언리얼, 텍스처는 흰색 | Painter 에서 색까지 칠하기 | 텍스처 한 벌로 모든 색. 색 바꿀 때 Painter 불필요 |
| 두께 맵으로 색·투명 계산 | 투명도 한 값 | 젤리의 "얇으면 밝고 두꺼우면 진함"이 두께 없이는 안 나옴 |
| Thin Translucent | 일반 Translucent / Subsurface | 뒤 배경이 젤리 색으로 물듦. Translucent 는 창백, Subsurface 는 불투명해 보임 |
| 하이라이트를 머티리얼에서 직접 그림 | 조명만 믿기 | 반투명은 태양빛 반사만 받아서 레퍼런스 같은 큰 흰 반사가 안 생김 |
| Tri-planar 마스크 | UV 기준 마스크 | 자동 UV 의 이음새를 숨기고 흘러내림 방향이 일정 |
| 붓 자국 텍스처 + Kuwahara 필터 | 둘 중 하나만 | 텍스처만은 무늬 같고, 필터만은 흐린 사진 같음 |
| 별을 표면에 붙인 스프라이트로 | 반사 방향으로 계산 | 곰처럼 둥근 물체에선 반사 방향 별이 1~3픽셀로 줄어 안 보임 |
| 스텐실로 필터 범위 제한 | 화면 전체 필터 | 배경·UI 까지 뭉개지는 것 방지 |

---

## 참고

- 수식·노드·HLSL 전체: [JellyMaterialGuide.ko.md](JellyMaterialGuide.ko.md)
- 결과 비교 이미지: `Docs/SubstancePainterMCP/images/`
- 폴더 구조 (`Tools/BuildJellyLookDev.py` 도 같은 경로를 씀)

  | 폴더 | 들어 있는 것 |
  |---|---|
  | `Art/Characters/Jelly` | 메시 |
  | `Art/Textures/Jelly` | 텍스처 |
  | `Art/Materials/Jelly` | 마스터 머티리얼 `M_Jelly_Gummy` |
  | `Art/Materials/Jelly/Instances` | 인스턴스 `MI_Jelly_*` |
  | `Art/Materials/PostProcess` | 그림체 필터 |
  | `Art/Materials/LookDev` | 룩데브 바닥 |
