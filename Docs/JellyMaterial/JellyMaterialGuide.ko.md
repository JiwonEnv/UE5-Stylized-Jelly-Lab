# 젤리 머티리얼 따라하기 가이드 (Substance 3D Painter 12 → Unreal Engine 5.8)

이 문서는 `L_JellyLookDev` 레벨의 젤리 곰들을 **손으로 다시 만들 때** 따라 할 순서입니다.
모든 수치는 실제로 쓰인 스크립트(`Tools/painter_scripts/10_build_jelly_stack.py`, `Tools/BuildJellyLookDev.py`)와 같습니다.

![결과](../SubstancePainterMCP/images/jelly_brush_v1.png)

---

## 0. 전체 흐름

```
메시(SM_GummyBear.obj)
  └─ Painter: 메시 맵 베이크 → 레이어 12개 → 커스텀 프리셋으로 내보내기
        GummyBear_BaseColor.png   (색 얼룩/홈 농도, 거의 흰색 = "틴트")
        GummyBear_Normal.png      (Height → DirectX Normal)
        GummyBear_Mask.png        R 두께 / G 미사용 / B 기포 / A 손자국 얼룩
        GummyBear_Paint.png       R 붓 결 / G 물감 덩어리
  └─ 붓질 텍스처 JellyBrushStrokes.png  (R 붓 자국 ID / G 하이라이트 대시 / B 붓 결)
Unreal:
  M_Jelly_Gummy (Thin Translucent 마스터)  →  MI_Jelly_* (색·스타일 프리셋)
  M_PP_JellyPaintFilter (Kuwahara 유화 필터, 커스텀 스텐실 1 인 젤리에만)
```

핵심 원리 세 가지:

1. **색은 언리얼에서 정한다.** Painter BaseColor 는 거의 흰색 틴트이고, 젤리 색은 머티리얼 인스턴스의 `Jelly Color` 로 바꾼다. 텍스처 한 벌로 모든 색을 만든다.
2. **두께가 젤리의 전부다.** 얇은 곳(귀·발끝)은 밝고 투명, 두꺼운 곳(배)은 진하고 탁하게. Painter 의 Thickness 를 Mask R 로 넘긴다.
3. **배경이 젤리 색으로 물들어야 한다.** 일반 Translucent 는 뒤 배경을 그대로 섞어서 창백해진다 → **Thin Translucent + Transmittance** 를 쓴다.

---

## 1. Substance 3D Painter

### 1-1. 새 프로젝트

| 항목 | 값 |
|---|---|
| 메시 | `SourceAssets/Characters/Jelly/SM_GummyBear.obj` (본인 메시도 OK, UV 필수) |
| Normal map format | **DirectX** (언리얼용) |
| Document resolution | 2048 |
| Import cameras | 끔 |

### 1-2. 채널 추가 (Texture Set Settings → Channels → `+`)

| 채널 | 포맷 | 이름(Label) | 용도 |
|---|---|---|---|
| Height | L16F | – | 굴곡/흘러내림 → Normal 로 변환 |
| Roughness | L8 | – | Painter 미리보기용 |
| User0 | L8 | Bubbles | 내부 기포 마스크 |
| User1 | L8 | Smudge | 손자국 얼룩 (언리얼 Roughness 가산) |
| User2 | L16 | Thickness | 두께 |
| User4 | L8 | BrushStrokes | 붓 결 |
| User5 | L8 | PaintDabs | 물감 덩어리 |

> ⚠️ **새 User 채널의 기본값은 흰색(1)** 입니다. 베이스 레이어에서 0 으로 덮지 않으면 마스크와 상관없이 전부 1로 내보내집니다. (실제로 겪은 버그)

### 1-3. 메시 맵 베이크 (Texture Set Settings → Bake Mesh Maps)

- 켤 것: **Thickness**, Curvature, Ambient Occlusion, Position, World Space Normal
- 하이폴리가 없으면 **Use Low Poly Mesh as High Poly Mesh** 체크
- Thickness `Max Distance` 를 올려야(상대값 0.3 정도) 배 부분까지 그라데이션이 생깁니다.
- 베이크 후 Texture Set Settings 의 Mesh maps 슬롯에서 Thickness 썸네일이 회색 그라데이션인지 확인하세요.

> ⚠️ 이 프로젝트에서는 Painter 12.2 의 레이 기반 베이커(Thickness/AO/Curvature)가 에러 없이 **빈 맵**을 냈습니다.
> 그래서 `Tools/BakeGummyBearMeshMaps.py` 로 SDF 에서 직접 계산한
> `SourceAssets/Characters/Jelly/MeshMaps/GummyBear_Thickness.png` 와 `GummyBear_Cavity.png` 를 리소스로 가져와 씁니다.
> 본인 메시가 정상 베이크되면 아래 표의 "비트맵" 대신 베이크된 메시 맵(Thickness / Curvature 제너레이터)을 쓰면 됩니다.
> 또 빈 Normal 메시 맵이 슬롯에 남아 있으면 내보낸 노멀이 모래처럼 깨지니, 비어 있으면 슬롯을 비우세요.

### 1-4. 레이어 스택 (아래 → 위 순서로 만들기)

모든 레이어는 **Fill Layer** 입니다. "켜는 채널"만 활성화하고 나머지는 끄세요(채널 버튼).
마스크는 **Add black mask → 마스크 안에 Fill 추가 → Grayscale 에 리소스 지정** 순서입니다.
`Tri-planar` 라고 적힌 마스크는 Fill 의 Projection 을 **Tri-planar projection** 으로 바꿉니다 (UV 섬이 많은 메시에서 이음새를 숨기고, 흘러내림이 항상 아래로 향하게 함).

| # | 레이어 이름 | 켜는 채널 = 값 | 레이어 불투명도 | 마스크 |
|---|---|---|---|---|
| 1 | Jelly Base | BaseColor `#FAF7F7`, Roughness 0.04, Height 0, User0 0, User1 0, User4 0, User5 0 | 100% | 없음 |
| 2 | Color Clouds Cool | BaseColor `#CCC7F2` (라벤더) | 55% | Clouds 2 · Tri-planar |
| 3 | Color Clouds Warm | BaseColor `#FFE0CC` (살구) | 45% | Clouds 3 · Tri-planar |
| 4 | Baked Thickness | User2 = **Thickness 맵** | 100% | 없음 (소스 자체가 두께 비트맵) |
| 5 | Cavity Density | BaseColor `#B8ADB8` | 60% | 오목한 곳 마스크 (Cavity 비트맵 또는 Curvature 제너레이터 반전) |
| 6 | Soft Lumps | Height 0.35 | 35% | 3D Perlin Noise Fractal |
| 7 | Drips | Height 0.6, Roughness 0.02 | 80% | Grunge Rusty Leaks · Tri-planar, 그 위에 **Position 제너레이터 (Multiply)** |
| 8 | Micro Ripples | Height 0.15 | 25% | Liquid · Tri-planar |
| 9 | Smudges | Roughness 0.22, User1 1.0 | 100% | Grunge Wipe Smudgy Heavy · Tri-planar, 마스크 Fill 불투명도 45% |
| 10 | Bubbles | User0 1.0, BaseColor 흰색(BaseColor 만 25%) | 100% | Gaussian Spots 1 · Tri-planar |
| 11 | Brush Strokes | User4 1.0 | 100% | Grunge Wipe Brushed Large · Tri-planar |
| 12 | Paint Dabs | User5 1.0 | 100% | Grunge Plaster Painted · Tri-planar |

포인트:

- **BaseColor 는 흰색에 가깝게** 유지합니다. 라벤더/살구 구름이 은은한 색 얼룩(레퍼런스의 보라·주황 기운)이 되고, 진짜 색은 언리얼에서 곱해집니다.
- **Height 는 약하게.** 젤리는 매끈해야 하이라이트가 또렷합니다. 언리얼 `Normal Strength` 로 한 번 더 줄입니다.
- Drips 의 Position 제너레이터는 위쪽만 남겨서 "위에서 흘러내리는" 느낌을 줍니다.

### 1-5. 내보내기 (Export Textures → Output Templates 에서 새 템플릿)

| 파일 | R | G | B | A |
|---|---|---|---|---|
| `GummyBear_BaseColor` | BaseColor R | BaseColor G | BaseColor B | – |
| `GummyBear_Normal` | Normal DirectX (Converted map: *Normal DirectX*) RGB | | | – |
| `GummyBear_Mask` | User2 (두께) | – | User0 (기포) | User1 (얼룩) |
| `GummyBear_Paint` | User4 (붓 결) | User5 (물감 덩어리) | – | – |

- PNG 8bit, Padding: Infinite (Dilation), Size 2048
- 출력 폴더: `SourceAssets/Characters/Jelly/Textures`

### 1-6. 붓질 텍스처

`JellyBrushStrokes.png` 는 Painter 가 아니라 `Tools/GenerateBrushStrokeTexture.py` 가 만듭니다 (타일링되는 붓 자국 1024²).
직접 그리고 싶다면 Photoshop/Procreate 로 1024² 타일 텍스처를 만들어 같은 채널 규칙으로 저장하면 됩니다.

- **R** = 붓 자국 하나하나가 서로 다른 단색 회색 (자국 ID)
- **G** = 짧고 가는 흰 대시 (하이라이트 획)
- **B** = 자국 방향을 따라가는 붓 결

---

## 2. Unreal Engine 5.8

### 2-1. 프로젝트 설정 (한 번만)

- **Project Settings → Rendering → Custom Depth-Stencil Pass = Enabled with Stencil** (`r.CustomDepth=3`).
  유화 필터가 "그림체 젤리만" 골라내는 데 필요합니다. 기본값(스텐실 없음)이면 필터가 아무 데도 안 걸립니다.

### 2-2. 임포트

| 에셋 | 설정 |
|---|---|
| `SM_GummyBear` | **Nanite 끄기** (반투명은 Nanite 폴백 메시 ≈3천 삼각형으로 그려져 각져 보임). 끈 뒤 메시가 다시 빌드되는지(삼각형 수 9만) 확인 |
| `T_GummyBear_BC` | sRGB 켬 |
| `T_GummyBear_N` | Compression = Normalmap |
| `T_GummyBear_Mask`, `T_GummyBear_Paint`, `T_GummyBear_Brush` (JellyBrushStrokes.png), `T_GummyBear_Stars` (JellyStarSparkles.png) | Compression = Masks, **sRGB 끔** |

### 2-3. 마스터 머티리얼 `M_Jelly_Gummy` — Details

| 항목 | 값 |
|---|---|
| Blend Mode | Translucent |
| Shading Model | **Thin Translucent** |
| Translucency → Lighting Mode | **Surface ForwardShading** |
| Refraction Method | Index of Refraction |
| Screen Space Reflections / Contact Shadows | 켬 |
| Allow Custom Depth Writes (Translucency) | **켬** (유화 필터 스텐실용) |

그래프에는 반드시 **Thin Translucent Material** 출력 노드가 정확히 하나 있어야 합니다 (두 개면 컴파일 실패, 없으면 기본 머티리얼로 대체).

### 2-4. 그래프를 단계별로 만들기

아래 식에서 `T` = 두께, `F` = Fresnel. 노드 이름은 언리얼 팔레트 이름 그대로입니다.

**① 두께 `T`**
```
F_view = OneMinus(Fresnel(Exponent 1.6))                 // 가운데 두껍고 가장자리 얇은 가짜 두께
T = Saturate( Lerp(Mask.R, F_view, FresnelThicknessWeight) + ThicknessBias )
```

**② 흡수색 (얇으면 밝고 진하면 깊게)** — 젤리 느낌의 핵심
```
Absorb = Power(JellyColor, T * Density + 0.35)
Body   = Lerp(Absorb, DeepColor, Power(T, 2.2)) * BaseColorTint.RGB      → Base Color
```

**③ 투과 (뒤가 물들게)**
```
Transmittance = Lerp(Absorb, DeepColor, T) * TransmissionBrightness  → Thin Translucent Material 노드
```

**④ 불투명도**
```
Opacity = Saturate( Lerp(OpacityThin, OpacityThick, T) + F * RimOpacity + 하이라이트 )   → Opacity
```
하이라이트·림·별 반짝이 값도 더해야 그 부분이 투명하게 사라지지 않습니다.

**⑤ 속에서 빛나는 느낌 (Emissive)**
```
Scatter = 0.3 + 0.7 * Power(1 - T, 1.4)
Emissive += InnerGlowColor * Absorb * Scatter * InnerGlow
```

**⑥ 스튜디오 하이라이트** — 반투명 Forward 셰이딩은 태양 스펙큘러만 받으므로 가짜 소프트박스 3개를 더함
```
R = ReflectionVectorWS
for D in (0.62,0.38,0.69), (0.80,-0.48,0.36), (-0.2,0.1,0.97)  (가중치 1, 0.55, 0.35):
    soft = Power(Saturate(Dot(R, D)), HighlightSharpness)
Emissive += Σ soft * HighlightIntensity
```

**⑦ Roughness / Normal / Refraction**
```
Roughness = Roughness + Mask.A * SmudgeRoughness
Normal    = Lerp((0,0,1), NormalTex, NormalStrength)
Refraction = IOR (1.33)
```

여기까지가 "사실적인 젤리" (`MI_Jelly_Raspberry` 등) 입니다. 아래는 스타일 옵션이며 **모두 기본값 0(꺼짐)** 으로 두고 인스턴스에서 켭니다.

**⑧ 다색 그라데이션 (그룹 Color Gradient)** — 핑크→보라→블루 곰
```
h    = Saturate((WorldPosition.z - ObjectPositionWS.z) / ObjectHeight)
low  = Lerp(BottomColor, MidColor, Saturate(h / BottomEnd))
grad = Lerp(low, JellyColor, Saturate((h - TopStart) / TopWidth))
core = Lerp(1, SmoothStep(0.35, 0.8, T), GradientCoreOnly)      // 두꺼운 몸통에만
JellyColor = Lerp(JellyColor, grad, GradientAmount * core)       // ②보다 먼저 적용
```

**⑨ 두 색 림 라이트 + 무지개빛 (그룹 Rim / Iridescence)**
```
side = Saturate(Dot(VertexNormalWS, (0,1,0.25)) * 0.6 + 0.5)
rim  = Power(Fresnel(Exp 1), RimPower)
Emissive += RimColorA*RimLightA*rim*side + RimColorB*RimLightB*rim*(1-side)
rainbow = 0.5 + 0.5 * Cos(Fresnel*IridScale + IridOffset + (0, .33, .67))     // Cosine 노드 Period 1
Emissive += rainbow * Power(Fresnel, 1.6) * Iridescence
```

**⑩ 그림체 (그룹 Painterly)**
- 계단 음영: `T = Saturate(Lerp(T, Floor((T + 붓 흔들림) * Bands + 0.5) / Bands, PaintStyle * PaintBanding))`
  > ⚠️ **Saturate 필수.** 붓 흔들림 때문에 0~1 밖으로 나가면 `Power(음수)` = NaN → 블룸으로 번진 초록 얼룩이 생깁니다 (실제로 겪음).
- 셀 톤: `NdotL = Dot(VertexNormalWS, (0.55,0.35,0.76)) + 붓 흔들림` → SmoothStep 두 단계로 ShadowTone / 1 / LightTone 을 곱함
- 외곽 톤: `Lerp(Body, Body*OutlineColor, SmoothStep(0.55,0.8,F) * OutlineAmount)`
- 페인트 하이라이트: ⑥의 `soft` 대신 `SmoothStep(0.915, 0.93, Dot(R,D) + Noise*0.025)` (또렷하고 살짝 일그러진 모양) — `Lerp(soft, painted, PaintStyle)`

**⑪ 붓 자국 (그룹 Brush Strokes)** — 레퍼런스 사과의 "붓질 단위 색 면"
- `JellyBrushStrokes` 를 **오브젝트 공간 Tri-planar** 로 샘플: `p = (WorldPosition - ObjectPositionWS) / BrushScale(42)`,
  YZ/XZ/XY 세 번 샘플 → `Power(Abs(VertexNormalWS), 4)` 정규화 가중치로 합침 → `S`
- **색 면 끊기**: 붓 흔들림에 `(S.R - 0.5) * BrushPatchBreakup * BrushAmount` 를 더함 → 계단·셀 경계가 붓 자국 모양으로 끊김
- **자국마다 색 흔들기**: `S.R > 0.62` 인 자국엔 BrushHueA(라벤더), `< 0.36` 인 자국엔 BrushHueB(살구)를 곱함
- **붓 결**: `Body *= Lerp(1, 0.82 + 0.36*S.B, Bristle*BrushAmount)`
- **흰 대시 하이라이트**: 하이라이트보다 넓은 영역(`SmoothStep(0.70,0.74, Dot(R,D))`) 안에서 `S.G * DashHighlights` 를 하이라이트에 더함

**⑫ 별 반짝이 + 유리 테두리 (그룹 Sparkle / Edge)** — 자세한 설명은 [6장](#6-별-반짝이-하이라이트-만들기)
- 별: `JellyStarSparkles` 를 ⑪과 같은 **오브젝트 공간 Tri-planar**(가중치 `Abs(N)^8`)로 샘플, `p / (StarSize*22)`
  - `Star Points` 0 → B(사각 글린트), 4 → R(4각 별), 6 → G(6각 별) 사이를 Lerp
  - 하이라이트 쪽에서만: `zone = SmoothStep(StarZone, StarZone+0.2, Max(Dot(R,D1), Dot(R,D2)))`
  - `Emissive += StarColor * shape * zone * StarGlint * 4`, 불투명도에도 더하기
- 테두리 선: `SmoothStep(0.45,0.55,F) * (1 - SmoothStep(0.72,0.82,F)) * EdgeLine` → Emissive, 불투명도에도 더하기

### 2-5. 유화 필터 `M_PP_JellyPaintFilter`

1. Material Domain = **Post Process**, Blendable Location = **Scene Color After Tonemapping**
2. 노드: `SceneTexture:PostProcessInput0`, `SceneTexture:CustomStencil`, 파라미터 `Brush Radius`(4), `Filter Strength`(1)
3. **Custom** 노드 (Output Float3, 입력 `Scene`, `Radius`) 에 Kuwahara 코드:

```hlsl
float2 texel = View.BufferSizeAndInvSize.zw;
float2 uv = GetDefaultSceneTextureUV(Parameters, 14);
int r = (int)clamp(Radius, 1.0, 8.0);
float3 m[4]; float3 s2[4];
for (int q = 0; q < 4; q++) { m[q] = 0; s2[q] = 0; }
for (int j = -r; j <= r; j++) for (int i = -r; i <= r; i++) {
    float3 c = SceneTextureLookup(uv + float2(i, j) * texel, 14, false).rgb;
    if (i <= 0 && j <= 0) { m[0] += c; s2[0] += c * c; }
    if (i >= 0 && j <= 0) { m[1] += c; s2[1] += c * c; }
    if (i <= 0 && j >= 0) { m[2] += c; s2[2] += c * c; }
    if (i >= 0 && j >= 0) { m[3] += c; s2[3] += c * c; }
}
float n = (r + 1) * (r + 1);
float best = 1e9; float3 res = Scene;
for (int k = 0; k < 4; k++) {
    float3 mu = m[k] / n; float3 v = abs(s2[k] / n - mu * mu);
    float sv = v.r + v.g + v.b;
    if (sv < best) { best = sv; res = mu; }
}
return res;
```

4. 마스크: `Saturate(1 - Abs(CustomStencil.R - 1))`
   × `1 - SmoothStep(0.78, 0.92, Luminance(Scene)) * PreserveHighlights` (밝은 하이라이트·별은 필터에서 빼서 또렷하게 유지)
   → `Lerp(Scene, Kuwahara, mask * FilterStrength)` → Emissive Color
5. 레벨에 **Post Process Volume** (Infinite Extent/Unbound 켬) → Post Process Materials 에 이 머티리얼 추가
6. 그림체로 보일 젤리 액터: **Render CustomDepth Pass 켬, CustomDepth Stencil Value = 1**

> 반경이 크면(6 이상) 하이라이트·눈코까지 뭉개집니다. 4 가 균형점이었습니다.
> 확인용으로 `Ignore Stencil = 1` 이면 화면 전체에 필터가 걸립니다.

### 2-6. 인스턴스 프리셋 (`/Game/JellyGame/Art/Jelly/MI_Jelly_*`)

색 값은 Linear RGB 입니다.

| 프리셋 | Jelly Color | Deep Color | Density | 켜는 옵션 |
|---|---|---|---|---|
| Raspberry | 0.95, 0.10, 0.14 | 0.40, 0.00, 0.04 | 1.6 | – |
| Orange | 1.00, 0.42, 0.04 | 0.65, 0.12, 0.00 | 1.4 | – |
| Teal | 0.10, 0.62, 0.66 | 0.01, 0.20, 0.26 | 1.5 | – |
| Blue | 0.18, 0.55, 1.00 | 0.02, 0.14, 0.55 | 1.5 | – |
| PinkIridescent | 1.00, 0.36, 0.76 | 0.85, 0.08, 0.50 | 1.3 | Gradient(보라·블루, Core Only), Rim A 노랑 4.0 / B 시안 0.7, Iridescence 0.25, Transmission 0.5 |
| PinkPainted | 1.00, 0.62, 0.75 | 0.92, 0.38, 0.55 | 0.8 | Paint 1, Cel 1, 라벤더 그림자, Brush 1 (Patch 0.45, Hue Jitter 0.8), Dash 1.3, Outline 0.3, + 유화 필터 |
| AmberPainted | 1.00, 0.70, 0.10 | 0.80, 0.36, 0.02 | 1.6 | Paint 1, Cel 1, Outline 1.0 주황, Brush 1, Dash 1.0, **6각 별** (Glint 3, Size 1.8, Zone 0.3), Edge 0.4, + 유화 필터 |
| RedPainted | 0.90, 0.05, 0.06 | 0.35, 0.00, 0.02 | 1.8 | 그림체(Paint/Cel/Brush/진한 Outline) **+ 이리데센트 조명**(5장) **+ 4각 별**, + 유화 필터 |

새 색을 만들 땐 **Jelly Color 와 Deep Color 두 개만** 바꾸면 됩니다 (Deep 은 Jelly 를 어둡고 채도 높게).

---

## 3. 겪은 함정 정리

| 증상 | 원인 | 해결 |
|---|---|---|
| 회색·창백한 젤리 | Translucent 는 배경을 물들이지 않음 | Thin Translucent + Transmittance |
| 각진 실루엣 | 반투명 + Nanite = 폴백 메시 | Nanite 끄고 메시 리빌드 확인 |
| 모래 같은 표면 | 빈 Normal 메시 맵이 내보내기에 섞임 | 빈 메시 맵 슬롯 비우기 |
| 머티리얼 전체가 기본 회색 | Thin Translucent 출력 노드 중복/누락 | 출력 노드 정확히 1개 |
| 초록 빛 얼룩 | `Power(음수)` NaN 이 블룸으로 번짐 | 계단 음영 결과 Saturate |
| 유화 필터 안 걸림 | 커스텀 스텐실 미기록 | `r.CustomDepth=3` + Allow Custom Depth Writes |
| 새 User 채널이 전부 1 | 새 채널 기본값이 흰색 | 베이스 레이어에서 0 지정 |
| 별 반짝이가 안 보임 | 반사 공간 별은 곡면에서 1~3px 로 줄어듦 | 오브젝트 공간 별 스프라이트 (6장) |
| 테두리 선이 안 보임 | Fresnel 0.8~0.95 띠는 실루엣 1~2px | 0.45~0.82 로 넓힘 |
| 빨강이 회색빛 분홍으로 바램 | 투과를 낮추고 불투명도를 올리면 칙칙한 BaseColor 가 드러남 | Transmission 0.45 / Opacity 0.85 유지, 림 Power 2.5 이상 |
| Kuwahara 가 하이라이트를 뭉갬 | 필터는 밝은 점도 평균 냄 | 밝기 0.78 이상은 필터 제외 (Preserve Highlights) |

---

## 4. 자동으로 다시 만들기

```bash
Tools/.jellyvenv/Scripts/python Tools/GenerateGummyBearMesh.py        # 곰 메시
Tools/.jellyvenv/Scripts/python Tools/BakeGummyBearMeshMaps.py        # 두께/곡률/AO
Tools/.jellyvenv/Scripts/python Tools/GenerateBrushStrokeTexture.py   # 붓질 텍스처
Tools/.jellyvenv/Scripts/python Tools/GenerateStarSparkleTexture.py   # 별 반짝이 스프라이트
python Tools/substance-painter-remote-mcp/sp_run.py Tools/painter_scripts/10_build_jelly_stack.py   # Painter 레이어
python Tools/substance-painter-remote-mcp/sp_run.py Tools/painter_scripts/20_export.py              # 내보내기
python Tools/ue_run.py Tools/BuildJellyLookDev.py                                                   # 언리얼 전체
```

Painter 는 `--enable-remote-scripting` 으로, 언리얼은 Python **Remote Execution** 을 켠 상태여야 합니다.

---

## 5. 그림체 + 이리데센트 합치기 (`MI_Jelly_RedPainted`)

![이리데센트 / 그림체+이리데센트 / 그림체+6각 별](../SubstancePainterMCP/images/jelly_iridescent_painted_v1.png)

마스터 머티리얼 하나에 모든 기능이 들어 있으니, **합치는 건 인스턴스에서 두 프리셋의 그룹을 같이 켜는 것**입니다.
`MI_Jelly_PinkIridescent` 에서 "여러 색의 빛"을 만드는 건 세 그룹입니다.

| 그룹 | 하는 일 | RedPainted 에 넣은 값 |
|---|---|---|
| Color Gradient | 두꺼운 몸통 안쪽만 위→아래로 다른 색 | Amount **0.35**, Core Only 1, Mid `0.70,0.02,0.30`(자홍), Bottom `0.28,0.12,0.85`(보라), Bottom End 0.08, Top Start 0.18, Top Width 0.25 |
| Rim / Iridescence – Rim | 한쪽 가장자리 금색, 반대쪽 파랑 | Rim A **3.0** `1.0,0.72,0.05`, Rim B **1.2** `0.45,0.65,1.0`, Rim Power **2.5** |
| Rim / Iridescence – Iridescence | 보는 각도에 따라 무지개 기운 | **0.15** |

따라 하기 (에디터에서 직접):

1. `MI_Jelly_RedPainted` 를 열고 Painterly / Brush Strokes 그룹은 그대로 둔다 (그림체 유지).
2. Color Gradient 를 켜되 **Amount 를 0.3~0.4 로 낮게.** 1.0 이면 빨강이 보라에 묻힌다 (PinkIridescent 는 원래 핑크라 1.0 이 괜찮았음).
3. Rim A/B 를 켜고 **Rim Power 를 2.5 이상**으로. 낮으면(1.5) 금색+파랑이 몸통 안까지 퍼져서 회색빛으로 섞인다.
4. Iridescence 는 0.1~0.2 만. 그림체 위에 무지개가 세면 지저분해진다.
5. **Transmission Brightness 0.45 / Opacity Thick 0.85 를 유지.** 투과를 0.3 아래로 내리고 불투명도를 0.9 위로 올리면 칙칙한 BaseColor 가 드러나 빨강이 회색빛 분홍이 된다 (실제로 겪음).
6. 별 반짝이와 테두리 선은 6장.

> 다른 그림체 프리셋(Amber/Pink)에도 같은 순서로 Gradient → Rim → Iridescence 를 얹으면 됩니다.
> 기준: **주색이 화면의 60% 이상**을 차지하게 Gradient Amount 를 고르고, 림은 가장자리 한 뼘 안에만 있게 Power 를 고릅니다.

---

## 6. 별 반짝이 하이라이트 만들기

레퍼런스 두 장의 반짝이는 성격이 다릅니다.

| 레퍼런스 | 반짝이 종류 | 이 프로젝트에서 |
|---|---|---|
| 앰버 사과 | 하이라이트 위에 **6각 별** 하나, 작은 별 몇 개 | `Star Points 6`, Glint 3, Size 1.8 (`MI_Jelly_AmberPainted`) |
| 파란 사과 | **작은 사각 점** 하이라이트 + 실루엣 안쪽의 **얇은 흰 테두리** + 두꺼운 투명 가장자리 | `Star Points 0`(사각 글린트) + `Edge Line` |

### 6-1. 왜 "별 스프라이트를 표면에 붙이는" 방식인가

처음엔 하이라이트처럼 **반사 벡터 공간**에 별 모양 함수를 그렸습니다 (카메라가 움직이면 별이 표면 위를 미끄러지는 진짜 반짝이).
그런데 곰처럼 곡률이 큰 메시에서는 반사 벡터가 픽셀마다 크게 바뀌어서 **별이 1~3픽셀로 쪼그라들어 보이지 않았습니다** (디버그 뷰로 확인).
그래서 **별 모양 텍스처를 오브젝트 공간에 드문드문 붙이고, 하이라이트가 비치는 쪽에서만 보이게** 바꿨습니다. 크기가 일정하고 모양이 또렷합니다.

### 6-2. 별 텍스처 만들기 (`JellyStarSparkles.png`, 1024², 검은 배경)

`Tools/GenerateStarSparkleTexture.py` 가 만듭니다. 직접 그린다면:

- **R** = 4각 별 7개 (십자, 가는 광선 + 작은 둥근 코어)
- **G** = 6각 별 7개
- **B** = 작은 사각 점 14개 (파란 사과의 네모 하이라이트)
- 별끼리 넉넉히 떨어뜨리고, 가장자리에 걸친 별은 반대편으로 이어지게(타일링)
- 별 모양 공식: `r / (코어 + (1-코어) * |cos(θ·N/2)|^날카로움)` 를 1에서 뺀 값 — N=4/6, 코어 0.2, 날카로움 10~14
- Photoshop/Procreate 에서 "Sparkle" 브러시로 검은 캔버스에 찍어도 됩니다. 텍스처 하나에 별이 **너무 많으면 패턴처럼 보이니** 채널당 5~10개.

> Substance Painter 로 하고 싶다면: User 채널 하나를 추가하고 Paint 레이어에서 별 알파(Shape → Star 또는 직접 만든 알파)로 하이라이트 자리에 몇 개만 찍어 Mask 의 빈 채널(G)로 내보내면 됩니다.
> 이 방식은 별 위치가 고정(카메라를 돌려도 그 자리)이라 그림 같은 느낌이 강하고, 위 텍스처 방식은 자동 배치라 메시를 바꿔도 다시 그릴 필요가 없습니다.

### 6-3. 머티리얼 노드 (그룹 Sparkle / Edge)

```
p      = (WorldPosition - ObjectPositionWS) / (StarSize * 22)
w      = Abs(VertexNormalWS)^8 / Dot(Abs(N)^8, 1)            // 날카로운 Tri-planar 가중치(별이 겹쳐 보이지 않게)
S      = Tex(p.yz)*w.x + Tex(p.xz)*w.y + Tex(p.xy)*w.z
shape  = Lerp( Lerp(S.B, S.R, Saturate(StarPoints/4)), S.G, Saturate((StarPoints-4)/2) )
zone   = SmoothStep(StarZone, StarZone+0.2, Max(Dot(R, D1), Dot(R, D2)))   // D = 소프트박스 하이라이트 방향
Emissive += StarColor * shape * zone * StarGlint * 4
Opacity  += shape * zone * StarGlint                                       // 별이 투명하게 사라지지 않게
```

| 파라미터 | 의미 | 추천 |
|---|---|---|
| Star Glint | 밝기 (0 = 끔) | 2~3 |
| Star Size | 별 크기 / 간격 (클수록 크고 드묾) | 1.5~2 |
| Star Points | 0 사각 / 4 십자 / 6 육각 | 앰버 6, 레드 4, 파란 사과풍 0 |
| Star Zone | 하이라이트에서 얼마나 멀리까지 별을 허용 | 0.3 (낮을수록 넓게 퍼짐) |
| Star Color | 별 색 | 흰색~연노랑 |

### 6-4. 파란 사과의 얇은 흰 테두리 (Edge Line)

```
F    = Fresnel(Exponent 1)
line = SmoothStep(0.45, 0.55, F) * (1 - SmoothStep(0.72, 0.82, F))   // 실루엣 "조금 안쪽" 띠
Emissive += EdgeLineColor * line * EdgeLine,  Opacity += line * EdgeLine
```

띠를 0.8~0.95 처럼 실루엣 끝에 두면 1~2픽셀이라 안 보입니다 (실제로 겪음).

### 6-5. 유화 필터와 같이 쓸 때

Kuwahara 는 주변 평균으로 칠하기 때문에 작은 별과 하이라이트를 지워 버립니다.
`M_PP_JellyPaintFilter` 의 **Preserve Highlights = 1** 이면 밝기 0.78 이상인 픽셀은 필터에서 빠져 원본 그대로 남습니다 — 붓질 몸통 위에 또렷한 별이 얹힌 그림이 됩니다.

### 6-6. 더 나아가려면

- **반짝이는 애니메이션**: `zone` 에 `0.5 + 0.5*Sin(Time*3 + S.R*20)` 같은 값을 곱하면 별마다 다른 박자로 깜빡입니다.
- **카메라를 따라 움직이는 반짝이**: 크고 매끈한 오브젝트(구, 사과)라면 6-1 의 반사 공간 방식이 더 사실적입니다 — 곡률이 완만해서 별이 충분히 크게 나옵니다.
- **파티클 반짝이**: 게임 연출용으로 더 크고 확실한 별이 필요하면 Niagara 스프라이트(별 텍스처, Additive)를 젤리 하이라이트 위치에 붙이는 방법도 있습니다.
