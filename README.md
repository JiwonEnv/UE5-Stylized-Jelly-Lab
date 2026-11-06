# UE5-Stylized-Jelly-Lab

Unreal Engine 5 기반 스타일라이즈드 젤리 아트 연구. 젤리 머티리얼, 셰이딩, 말랑한 변형 표현과 Substance Painter 연동 파이프라인 실험.

## 현재 상태
UE **5.8.4**의 Blueprint 기반 프로젝트를 생성했습니다. 표시 이름은 **Jelly Game**, 프로젝트 파일은 `JellyGame.uproject`입니다. Painter에서 베이킹한 메시·텍스처를 가져와 PBR 머티리얼을 연결한 테스트 레벨까지 구성했습니다. 캐릭터 이동·젤리 변형·게임플레이는 아직 구현하지 않았습니다.

저장소 이름은 `UE5-Stylized-Jelly-Lab`이며, 로컬 폴더 이름은 `Unreal-Engine-5-Jelly-Game`입니다. `JellyGame`은 Unreal 프로젝트 파일 이름 및 콘텐츠 네임스페이스입니다.

## 개발 방향
- Blueprint 우선, 성능 측정이나 기능 요구로 필요해질 때 C++ 도입
- WPO: 대기·이동 중 미세한 출렁임과 표면 표현
- 충돌 이벤트 + 스프링: 점프·착지·벽 충돌 시 메시 또는 본의 스쿼시·스트레치
- 초기 충돌 판정은 안정적인 캡슐을 유지하고 시각적 메시를 변형

## 폴더
| 경로 | 용도 |
| --- | --- |
| Config/ | Unreal 프로젝트 설정 |
| Content/JellyGame/Art/ | 캐릭터, 환경, 머티리얼, 텍스처, VFX |
| Content/JellyGame/Blueprints/ | 캐릭터 및 공용 컴포넌트 |
| Content/JellyGame/Core/ | GameMode, Controller 등 기반 시스템 |
| Content/JellyGame/Gameplay/ | 상호작용과 게임 규칙 |
| Content/JellyGame/Physics/ | 변형 프로필 등 물리 반응 에셋 |
| Content/JellyGame/Maps/ | 게임 및 테스트 레벨 |
| Content/JellyGame/Experiments/ | 검증 전 실험 |
| Content/JellyGame/UI/ | 위젯 및 UI 에셋 |
| SourceAssets/ | Blender·PSD 등 원본 제작 파일 |
| Source/ | 향후 C++ 도입 시 사용; 현재 빈 자리 |
| Docs/ | 설계와 개발 규칙 |

빈 폴더는 `.gitkeep`으로 유지합니다. 실제 파일이 생기면 해당 `.gitkeep`을 제거해도 됩니다. 에셋 이동·이름 변경은 Unreal Content Browser에서 수행하고 Redirector를 정리합니다.

## 시작 방법
1. UE 5.8.4로 `JellyGame.uproject`를 엽니다. 시작 맵은 `Content/JellyGame/Maps/L_PainterMaterialTest`입니다.
2. Painter 테스트 에셋은 `Content/JellyGame/Experiments/PainterPipeline`에 있습니다. `M_PainterTest`는 BaseColor, DirectX Normal, ORM(R=AO/G=Roughness/B=Metallic)을 연결합니다.
3. Python Editor Script Plugin과 Editor Scripting Utilities를 활성화했습니다. 재현 도구는 `Tools/SetupPainterMaterialUE.py`, 검증 기록은 `Docs/SubstancePainterMCP/ue5-validation.json`입니다.
4. [Painter → UE5 실습 글](Docs/SubstancePainterMCP/painter-to-ue5.ko.md)을 참고하고, [하이브리드 설계](Docs/JellySystem.md)에 따라 캐릭터 이동·점프와 젤리 변형을 추가합니다.

## Git 및 LFS
Unreal 패키지와 주요 바이너리 아트 에셋은 `.gitattributes`의 Git LFS 규칙으로 관리합니다.

첫 커밋 전 `git status`, `git check-ignore`, `git check-attr filter -- <asset-path>`, `git lfs ls-files`로 추적 대상을 확인합니다. LFS 원격 지원과 용량을 확인하고, 공동 편집하는 Unreal 패키지는 서버가 지원할 때 잠금을 사용합니다. 기존 바이너리 이력이 생긴 뒤 LFS로 옮기는 이력 재작성은 별도 검토합니다.

[에셋 네이밍](Docs/AssetNaming.md) · [커밋 및 협업 규칙](Docs/CommitConvention.md)

## 개발 순서
젤리 머티리얼 → 기본 캐릭터 이동·점프 → WPO → 충돌 기반 스프링 변형 → 게임플레이 프로토타입.

라이선스는 미정입니다. 외부 에셋의 출처와 사용 조건은 `Docs/ThirdPartyAssets.md`에 기록합니다.
