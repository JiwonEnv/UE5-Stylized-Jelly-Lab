# 에셋 네이밍

형식: `Prefix_DescriptiveName_Variant`. 영문 PascalCase와 숫자, 밑줄을 사용하고 공백·한글·특수문자는 파일 및 에셋 식별자에서 피합니다. 설명과 문서는 한국어를 사용해도 됩니다. 의미 없는 Final, New, Copy 대신 용도를 적습니다.

| 종류 | 접두사 | 예 |
| --- | --- | --- |
| Actor/Character Blueprint | BP_ | BP_JellyCharacter |
| Actor Component Blueprint | BPC_ | BPC_JellyDeformation |
| Blueprint Interface | BPI_ | BPI_JellyInteractable |
| Blueprint Function Library | BPFL_ | BPFL_JellyMath |
| Static / Skeletal Mesh | SM_ / SK_ | SM_JellyBody / SK_JellyCharacter |
| Skeleton / Physics Asset | SKEL_ / PHYS_ | SKEL_Jelly / PHYS_Jelly |
| Material / Instance / Function | M_ / MI_ / MF_ | M_JellyMaster / MI_JellyBlue / MF_JellyWobble |
| Texture | T_ | T_JellyNoise |
| Niagara System / Emitter | NS_ / NE_ | NS_JellyLanding / NE_JellyDroplets |
| Animation / Anim Blueprint | A_ / ABP_ | A_JellyJump / ABP_Jelly |
| Widget Blueprint | WBP_ | WBP_MainHUD |
| Level | L_ | L_JellyPlayground |
| Data Asset / Data Table | DA_ / DT_ | DA_JellySpringProfile / DT_JellyStats |
| Enum / Struct | E_ / ST_ | E_JellyState / ST_JellyImpact |
| Input Action / Mapping Context | IA_ / IMC_ | IA_Jump / IMC_Jelly |

텍스처 역할 접미사: `_BC`(Base Color), `_N`(Normal), `_R`(Roughness), `_M`(Metallic), `_AO`, `_ORM`(R=AO/G=Roughness/B=Metallic). 채널 패킹이 다르면 문서에 명시합니다.

자체 에셋은 `Content/JellyGame`에 저장합니다. 외부 패키지는 원래 구조와 라이선스를 유지하고 자체 제작 에셋과 구분합니다. 실험은 `Experiments/<Topic>`에 두며 검증 후 정식 경로로 이동합니다. 파일 탐색기로 `.uasset`을 이동하지 말고 에디터에서 이동한 뒤 참조와 Redirector를 확인합니다.
