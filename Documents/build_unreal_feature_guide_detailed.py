from pathlib import Path
import importlib.util
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r"E:\Project\Unreal-Engine-5-Jelly-Game")
DOCS = ROOT / "Documents"
OUT = DOCS / "언리얼_기능_상세_정의와_사용_가이드.docx"
IMG = DOCS / "ue_feature_images"

# 기존 문서의 21개 기능 정의를 데이터 원본으로 재사용한다.
spec = importlib.util.spec_from_file_location("base_guide", DOCS / "build_unreal_feature_guide.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
features = base.features

details = {
"액터와 컴포넌트": ("레벨 에디터의 Outliner와 Details 패널. 새 설계는 Content Browser의 Add(+) > Blueprint Class에서 만든다.", ["Blueprint Class에서 Actor 또는 Character 부모 클래스를 선택한다.", "Components 패널에서 Skeletal Mesh, Capsule Collision, Audio, Niagara 등 필요한 부품을 추가한다.", "컴포넌트 이름을 역할 중심으로 바꾸고 부모·자식 구조를 확인한다.", "Details에서 위치와 속성을 조정한 뒤 레벨로 끌어 놓아 시험한다."], "Actor는 레벨에 존재하는 완성 대상이고 Component는 그 안에서 한 가지 기능을 담당한다. Transform, Tick, Mobility와 컴포넌트 계층을 먼저 확인한다."),
"스태틱 메시": ("Content Browser에서 Static Mesh 자산을 더블클릭하면 Static Mesh Editor가 열린다. 가져오기는 Add(+) 또는 Import를 사용한다.", ["FBX/OBJ 등 모델 파일을 Import한다.", "Static Mesh Editor에서 머티리얼 슬롯, UV 채널, Nanite 사용 여부를 확인한다.", "Collision 메뉴에서 단순 충돌을 만들고 Show > Simple Collision으로 모양을 검토한다.", "LOD 또는 자동 단순화를 설정하고 레벨에 배치해 크기와 충돌을 시험한다."], "머티리얼 슬롯, Collision Complexity, LOD Screen Size, Lightmap UV를 주로 본다. 움직일 수 있지만 뼈 애니메이션은 사용하지 않는 메시다."),
"스켈레탈 메시": ("Content Browser에서 Skeletal Mesh 자산을 더블클릭해 Skeletal Mesh Editor를 연다. FBX 가져오기에서 Skeletal Mesh와 필요 시 Import Morph Targets를 선택한다.", ["모델과 스켈레톤을 같은 기준 자세와 단위로 내보낸다.", "Import 창에서 사용할 Skeleton을 고르거나 새로 생성한다.", "에디터에서 Skin Weight, Section, Material, Morph Target 목록을 확인한다.", "Animation Blueprint와 Physics Asset을 연결해 실제 게임 자세를 시험한다."], "Skeleton, Physics Asset, Anim Class, LOD, Skin Weight가 핵심이다. 메시 외형·뼈·가중치는 서로 다른 데이터이므로 각각 검증한다."),
"스켈레톤과 본": ("Skeletal Mesh Editor의 Skeleton Tree 또는 Skeleton 자산 편집기에서 확인한다. 소켓은 Skeleton Tree에서 본을 우클릭해 추가한다.", ["DCC 도구에서 부모·자식 본 구조와 기준 자세를 확정한다.", "FBX 가져오기 후 Skeleton Tree에서 누락·이름 변경·축 방향을 확인한다.", "Preview Scene에서 본 표시를 켜고 움직임이 메시 가중치에 미치는 영향을 본다.", "재사용할 캐릭터끼리는 본 이름과 계층 규칙을 동일하게 유지한다."], "Root와 Pelvis/중심 본, 부모·자식 계층, Retargeting 옵션, 소켓 위치를 확인한다. 본 수가 늘면 제작과 런타임 비용도 증가한다."),
"모프 타깃": ("Skeletal Mesh Editor의 Morph Target Previewer 또는 Details의 Morph Target 목록. 가져올 때 FBX Import Options에서 Import Morph Targets를 켠다.", ["기본 메시의 복사본에서 꼭짓점 수와 순서를 유지한 채 목표 모양을 만든다.", "FBX로 내보내고 Skeletal Mesh 가져오기 또는 Reimport에서 Morph Target을 포함한다.", "Morph Target Previewer의 Weight를 0~1로 바꿔 단독·혼합 변형을 확인한다.", "Animation Blueprint의 Modify Curve 또는 Blueprint의 Set Morph Target으로 값을 구동한다."], "Name과 Weight가 핵심이며 값은 보통 0~1을 사용한다. 모프는 시각적 꼭짓점 변형이고 Collision을 자동 변경하지 않는다."),
"애니메이션 블루프린트": ("Content Browser의 Add(+) > Animation > Animation Blueprint. 생성 시 대상 Skeleton을 선택하며, Skeletal Mesh Component의 Anim Class에 지정한다.", ["Event Graph에서 Try Get Pawn Owner와 속도·공중 여부·충격량을 읽는다.", "Anim Graph에서 State Machine, Blend Space, Control Rig 또는 변형 노드를 연결한다.", "Preview Mesh로 포즈를 확인하고 Compile한다.", "캐릭터의 Skeletal Mesh Component > Animation > Anim Class에 설정한다."], "Event Graph는 상태값 준비, Anim Graph는 최종 포즈 생성 역할이다. 매 프레임 무거운 게임 규칙을 넣지 말고 자세 계산에 집중한다."),
"블루프린트": ("Content Browser의 Add(+) > Blueprint Class. 자산을 열면 Components, My Blueprint, Event Graph, Details 패널이 보인다.", ["목적에 맞는 부모 클래스(Actor, Character, Component 등)를 선택한다.", "변수와 컴포넌트를 먼저 정의하고 Event Graph에 최소 흐름을 만든다.", "자주 쓰는 로직은 Function이나 Macro로 분리하고 이름과 입력·출력을 명확히 한다.", "Compile 후 Play In Editor에서 Print String, Breakpoint, Watch Value로 검증한다."], "Event, Function, Variable, Construction Script, Class Defaults가 기본 요소다. Tick 남용과 거대한 한 장 그래프를 피한다."),
"C 플러스 플러스": ("Tools > New C++ Class 또는 Content Browser의 C++ Classes. 코드는 Source 폴더와 IDE에서 편집하고 Unreal Build Tool로 컴파일한다.", ["가장 가까운 Unreal 부모 클래스를 선택해 헤더와 소스 파일을 만든다.", "UCLASS, UPROPERTY, UFUNCTION으로 에디터와 Blueprint에 노출할 범위를 선언한다.", "빌드 후 에디터에서 파생 Blueprint를 만들어 조정 가능한 값만 노출한다.", "Unreal Insights로 실제 병목을 확인한 뒤 반복 계산이나 공통 기반 로직을 이동한다."], "C++는 엔진 확장성과 재사용에 유리하지만 컴파일과 메모리 안전 책임이 따른다. 빠른 시각 실험은 Blueprint와 혼합한다."),
"머티리얼": ("Content Browser의 Add(+) > Material. 자산을 더블클릭하면 Material Editor가 열리고, 노드 결과를 Main Material Node에 연결한다.", ["Base Color, Roughness, Normal 등 최소 PBR 입력부터 연결한다.", "색·강도·텍스처 중 반복 조절할 값은 Parameter로 변환한다.", "Preview Mesh와 실제 레벨 조명 양쪽에서 확인한다.", "Shader Complexity와 GPU 프로파일로 반투명·다층 계산 비용을 확인한다."], "Material Domain, Blend Mode, Shading Model과 Base Color/Roughness/Normal/Opacity 입력이 핵심이다. 표면 표현이며 질량이나 충돌 판정은 바꾸지 않는다."),
"머티리얼 인스턴스": ("기본 Material 자산을 우클릭 > Create Material Instance. 실행 중 변경은 Blueprint에서 Create Dynamic Material Instance를 사용한다.", ["부모 Material에서 필요한 값을 Scalar/Vector/Texture Parameter로 만든다.", "Material Instance를 생성하고 체크박스를 켜 해당 값만 덮어쓴다.", "캐릭터별 실시간 변화가 필요하면 시작 시 Dynamic Material Instance를 한 번 생성해 저장한다.", "Set Scalar/Vector Parameter Value로 젖음·먼지량·색을 변경한다."], "Parent와 Parameter Overrides를 확인한다. 매 프레임 새 인스턴스를 만들지 말고 생성한 객체를 재사용한다."),
"UV와 마스크": ("UV는 Static/Skeletal Mesh Editor의 UV 보기에서 확인한다. 마스크 텍스처는 Content Browser로 가져오고 Material Editor에서 Texture Sample로 사용한다.", ["DCC 도구에서 겹침과 이음새 목적을 정해 UV를 편다.", "메시 에디터에서 채널과 왜곡을 확인한다.", "흑백 또는 RGBA 채널에 젖음·먼지·노출 영역을 저장한다.", "Material에서 마스크를 Lerp의 Alpha로 연결하고 경계와 압축 손상을 확인한다."], "UV Channel, Texel Density, Seam, Address Mode, sRGB 설정을 본다. 데이터 마스크는 대개 sRGB를 끄고 용도에 맞는 압축을 사용한다."),
"Substrate": ("Edit > Project Settings > Engine > Rendering에서 Substrate 관련 설정을 확인한 뒤 Material Editor에서 Substrate 노드를 사용한다. 버전별 이름과 지원 상태를 확인한다.", ["프로젝트 복사본이나 실험 브랜치에서 기능을 활성화하고 에디터를 재시작한다.", "단일 Slab으로 기본 표면을 재현한 뒤 필요한 층만 추가한다.", "젤리·물막·오염층을 혼합하고 동일 조명에서 기존 Material과 비교한다.", "GPU 시간, 플랫폼 지원, 셰이더 컴파일 규모를 기록해 채택 여부를 결정한다."], "층 수와 혼합 방식이 늘수록 표현력과 비용이 함께 증가한다. 실험 기능 여부와 목표 플랫폼 지원을 해당 엔진 버전에서 반드시 확인한다."),
"Niagara": ("Content Browser의 Add(+) > FX > Niagara System. System Editor 안에서 Emitter, Particle Spawn/Update, Renderer와 Parameters를 편집한다.", ["템플릿 또는 빈 System을 만들고 Emitter를 추가한다.", "Spawn Rate/Burst, Lifetime, Velocity, Size를 작은 값부터 조정한다.", "Sprite/Mesh/Ribbon Renderer를 선택하고 User Parameter를 노출한다.", "Blueprint의 Niagara Component 또는 Spawn System 노드로 위치와 강도를 전달한다."], "System은 전체 효과, Emitter는 발생기, Module은 규칙, Renderer는 보이는 방식이다. 장식 입자를 게임의 권위 있는 판정으로 사용하지 않는다."),
"충돌": ("Edit > Project Settings > Engine > Collision에서 채널과 Preset을 관리한다. 각 Component의 Details > Collision에서 개별 반응을 설정한다.", ["Object Type과 상대 대상별 Block/Overlap/Ignore 요구를 표로 정한다.", "Project Settings에서 필요한 커스텀 채널과 Preset만 추가한다.", "Component에 Collision Enabled와 Preset을 지정한다.", "뷰포트의 Collision 표시와 이벤트 로그로 실제 Block/Overlap을 시험한다."], "Collision Enabled, Object Type, Preset, Response, Generate Overlap Events가 핵심이다. 모프에 맞춰 캡슐 크기를 바꿀 경우 서버 판정과 화면을 같은 상태값으로 갱신한다."),
"Chaos 물리": ("Component Details의 Physics와 Collision 항목, Skeletal Mesh용 Physics Asset Editor, Project Settings의 Physics/Chaos Solver에서 설정한다.", ["Simulate Physics를 켜기 전에 단순 충돌과 Mobility를 확인한다.", "Mass, Damping, Gravity, Constraint를 작은 범위에서 조정한다.", "Physics Asset에서는 몸체 수와 관절 한계를 최소 구성으로 만든다.", "서버·낮은 프레임·충돌 밀집 상황에서 안정성을 반복 시험한다."], "Mass, Damping, Sleep, Substepping, Constraint Limit가 주요 항목이다. 조작 캐릭터 전체보다 제한된 장식과 조각에 선택적으로 쓰는 편이 안전하다."),
"Chaos Flesh": ("Edit > Plugins에서 Chaos Flesh 플러그인을 확인한 뒤 관련 Flesh/Geometry Collection 자산과 Deformer Graph를 사용한다. 버전별 워크플로가 달라 공식 5.8 문서를 함께 본다.", ["플러그인을 활성화한 실험 프로젝트에서 단순한 젤리 형태로 시작한다.", "저해상도 볼륨 시뮬레이션 메시와 충돌 조건을 만든다.", "고해상도 표면에 변형 결과를 연결한다.", "같은 장면의 Morph 방식과 CPU 비용·안정성·네트워크 재현성을 비교한다."], "실험적·고비용 기능일 수 있으므로 목표 플랫폼과 엔진 버전 검증이 우선이다. 게임 판정은 별도 서버 상태로 단순화한다."),
"소켓과 부착": ("Skeletal Mesh/Skeleton Editor의 Skeleton Tree에서 Socket을 만든다. Blueprint에서는 Attach Actor/Component to Component와 Detach 노드를 사용한다.", ["따라갈 본을 우클릭해 Socket을 만들고 역할 중심 이름을 붙인다.", "Preview Asset을 연결해 상대 위치·회전을 조정한다.", "Blueprint에서 Parent, Socket Name, Location/Rotation Rule을 지정해 부착한다.", "분리 시 Detach 후 물리·효과·수명 처리를 명시한다."], "Snap to Target와 Keep Relative/World 규칙을 구분한다. 표면 임의 위치 부착은 소켓만으로 부족해 별도 좌표나 마스크가 필요하다."),
"네트워크 복제와 RPC": ("Actor/Component Details의 Replication, Blueprint Class Defaults의 Replicates, 변수 Details의 Replication, Custom Event의 Replicates 옵션에서 설정한다.", ["서버가 확정해야 하는 최소 상태를 먼저 목록화한다.", "Actor Replicates와 필요한 변수 RepNotify를 설정한다.", "클라이언트 입력 요청은 Server RPC로 보내고 서버에서 검증한다.", "받은 상태로 각 클라이언트가 Material·Animation·Niagara를 재생하도록 분리한다."], "Authority, Ownership, Replicated/RepNotify, Server/Client/Multicast RPC를 구분한다. 시각 입자 전체가 아니라 상태와 시드처럼 작은 데이터를 보낸다."),
"ISM과 HISM": ("Blueprint Components의 Instanced Static Mesh 또는 Hierarchical Instanced Static Mesh Component. Details나 Add Instance 노드로 인스턴스를 추가한다.", ["동일한 Static Mesh와 Material을 공유하는 반복 대상을 고른다.", "ISM/HISM Component를 추가하고 메시를 지정한다.", "Add Instance로 각 Transform을 넣고 개별 Actor 방식과 비교한다.", "인스턴스 선택·충돌·제거가 필요한 범위가 기능 제한과 맞는지 확인한다."], "Per Instance Transform, Cull Distance, Collision, Instance Count를 본다. 복잡한 개별 로직이 필요하면 일반 Actor가 더 적합할 수 있다."),
"LOD와 컬링": ("Static/Skeletal Mesh Editor의 LOD Settings, 각 Component의 Rendering/Cull Distance, Niagara의 Effect Type/Scalability에서 설정한다.", ["실제 관찰 거리와 화면 크기를 기준으로 품질 단계를 정한다.", "메시 LOD를 만들고 전환 지점의 실루엣 변화를 확인한다.", "작은 장식과 효과에 Cull Distance와 Niagara Scalability를 설정한다.", "Low~Epic 품질에서 게임 단서와 판정 공정성이 유지되는지 캡처 비교한다."], "Screen Size, Min LOD, Cull Distance, Visibility Based Anim Tick, Niagara Scalability가 주요 항목이다. 최적화가 게임 정보를 없애지 않게 한다."),
"프로파일링": ("Window > Developer Tools의 Output Log/Message Log, Tools의 Unreal Insights, 콘솔 명령 stat unit·stat gpu·stat net, ProfileGPU 등을 사용한다.", ["기준 장면과 최악 장면, 해상도, 품질, 플레이어 수를 고정한다.", "CPU Game/Render/RHI, GPU, 메모리, 네트워크를 분리해 측정한다.", "의심 기능을 한 번에 하나씩 끄고 켜며 차이를 기록한다.", "에디터 수치만 보지 말고 Development 또는 출시 설정에 가까운 빌드에서 재측정한다."], "평균 FPS 외에 프레임 시간과 긴 스파이크를 본다. Unreal Insights의 타임라인과 GPU Visualizer로 원인을 특정한 뒤 수정한다."),
}

def font(run, size=10.3, bold=False, color="202124"):
    run.font.name = "맑은 고딕"; run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    run.font.size = Pt(size); run.bold = bold; run.font.color.rgb = RGBColor.from_string(color)

def shade(cell, fill):
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), fill); cell._tc.get_or_add_tcPr().append(shd)

def line(doc, label, text):
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(6); p.paragraph_format.line_spacing=1.25
    font(p.add_run(label+"  "),10.3,True,"17365D"); font(p.add_run(text),10.3)

def bullets(doc, items, numbered=False):
    for i,item in enumerate(items,1):
        p=doc.add_paragraph(); p.paragraph_format.left_indent=Mm(7); p.paragraph_format.first_line_indent=Mm(-5); p.paragraph_format.space_after=Pt(4); p.paragraph_format.line_spacing=1.2
        font(p.add_run((f"{i}. " if numbered else "• ")+item),10.1)

def picture(doc, filename, caption, width=166):
    path=IMG/filename
    if not path.exists(): return
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(5); p.paragraph_format.space_after=Pt(3)
    r=p.add_run(); r.add_picture(str(path),width=Mm(width))
    c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after=Pt(8)
    font(c.add_run(caption),8.5,False,"666666")

doc=Document(); sec=doc.sections[0]
sec.top_margin=Mm(18); sec.bottom_margin=Mm(17); sec.left_margin=Mm(21); sec.right_margin=Mm(21)
normal=doc.styles["Normal"]; normal.font.name="맑은 고딕"; normal._element.rPr.rFonts.set(qn("w:eastAsia"),"맑은 고딕"); normal.font.size=Pt(10.3); normal.paragraph_format.line_spacing=1.24
for n,s in [("Title",27),("Heading 1",18),("Heading 2",12.5)]:
    st=doc.styles[n]; st.font.name="맑은 고딕"; st._element.rPr.rFonts.set(qn("w:eastAsia"),"맑은 고딕"); st.font.size=Pt(s); st.font.bold=True; st.font.color.rgb=RGBColor(0,0,0); st.paragraph_format.keep_with_next=True
header=sec.header.paragraphs[0]; header.alignment=WD_ALIGN_PARAGRAPH.RIGHT; font(header.add_run("Unreal Engine 5.8.4 기능 상세 가이드"),8.2,False,"777777")
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement("w:fldSimple"); field.set(qn("w:instr"),"PAGE"); footer._p.append(field)

p=doc.add_paragraph(style="Title"); font(p.add_run("언리얼 기능 상세 정의와 사용 가이드"),27,True,"000000")
p=doc.add_paragraph(); font(p.add_run("젤리 비주얼·물리 구현을 위한 입문자용 통합 문서"),14,True,"17365D")
line(doc,"대상 독자","언리얼을 처음 접하는 기획자, 아티스트, 사운드 및 제작 협업자")
line(doc,"기준 환경","JellyGame 프로젝트 · Unreal Engine 5.8.4 · 2026-11-06")
line(doc,"문서 구성","각 기능을 서로 합치지 않고 독립된 장으로 설명한다. 각 장에는 정의, 에디터 위치, 기본 사용 순서, 주요 항목, 프로젝트 적용 예, 주의점과 첫 실습이 포함된다.")
picture(doc,"01_unreal_editor_overview.jpg","그림 1. JellyGame 프로젝트의 Unreal Editor 전체 화면. 중앙은 Viewport, 오른쪽은 Outliner, 아래는 Content Browser이다.")
doc.add_paragraph("먼저 알아둘 화면",style="Heading 2")
bullets(doc,["Viewport: 레벨과 게임 대상을 눈으로 확인하고 배치하는 공간", "Outliner: 현재 레벨에 놓인 Actor 목록", "Details: 선택한 Actor·Component의 속성", "Content Browser/Drawer: 프로젝트 자산을 만들고 찾는 공간", "Toolbar: 저장, 실행(Play), 제작 모드와 주요 도구"])
doc.add_paragraph("기능 목록",style="Heading 2")
t=doc.add_table(rows=1,cols=2); t.style="Table Grid"; shade(t.rows[0].cells[0],"17365D"); shade(t.rows[0].cells[1],"17365D")
t.rows[0].cells[0].text="번호"; t.rows[0].cells[1].text="독립 기능 장"
for c in t.rows[0].cells:
    for r in c.paragraphs[0].runs: font(r,9,True,"FFFFFF")
for i,f in enumerate(features,1):
    c=t.add_row().cells; c[0].text=str(i); c[1].text=f["title"]+" · "+f["en"]
    if i%2==0: shade(c[0],"F3F6FA"); shade(c[1],"F3F6FA")
    c[0].paragraphs[0].alignment=WD_ALIGN_PARAGRAPH.CENTER
    for x in c:
        x.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for r in x.paragraphs[0].runs: font(r,9)

for idx,f in enumerate(features,1):
    doc.add_page_break()
    h=doc.add_paragraph(style="Heading 1"); font(h.add_run(f"{idx:02d}  {f['title']}"),18,True)
    p=doc.add_paragraph(); font(p.add_run(f["en"]),9.5,True,"666666")
    line(doc,"한 문장 정의",f["one"]); line(doc,"쉽게 비유하면",f["analogy"])
    loc,steps,keys=details[f["title"]]
    doc.add_paragraph("에디터에서 찾는 위치",style="Heading 2"); p=doc.add_paragraph(loc); p.paragraph_format.line_spacing=1.25
    if f["title"]=="블루프린트": picture(doc,"02_add_menu_closeup.jpg","그림 2. Content Browser의 Add 메뉴. Blueprint Class, Material, Niagara System 등을 여기서 만든다.",145)
    if f["title"]=="머티리얼": picture(doc,"../../Docs/SubstancePainterMCP/images/05-ue5-material-graph.png","그림 3. Material Editor의 노드 그래프 예시. 왼쪽 계산 결과를 오른쪽 Material 입력에 연결한다.",160)
    if f["title"]=="충돌": picture(doc,"04_collision_settings_closeup.jpg","그림 4. Project Settings > Engine > Collision. Object/Trace Channel과 Preset을 관리하는 위치이다.",160)
    if f["title"]=="네트워크 복제와 RPC": picture(doc,"03_project_settings_closeup.jpg","그림 5. Project Settings 화면. 프로젝트 공통 규칙은 좌측 분류에서 찾아 설정한다.",155)
    doc.add_paragraph("기본 사용 순서",style="Heading 2"); bullets(doc,steps,True)
    doc.add_paragraph("주요 항목과 읽는 법",style="Heading 2"); p=doc.add_paragraph(keys); p.paragraph_format.line_spacing=1.25
    doc.add_paragraph("JellyGame에서의 사용",style="Heading 2"); p=doc.add_paragraph(f["project"]); p.paragraph_format.line_spacing=1.25
    doc.add_paragraph("작동 원리",style="Heading 2"); bullets(doc,f["works"])
    doc.add_paragraph("주의와 흔한 오해",style="Heading 2"); p=doc.add_paragraph(f["not"]); p.paragraph_format.line_spacing=1.25
    doc.add_paragraph("첫 확인 실습",style="Heading 2"); p=doc.add_paragraph(f["first"]); p.paragraph_format.line_spacing=1.25

doc.add_page_break(); doc.add_paragraph("프로젝트 적용 권장 순서",style="Heading 1")
steps2=[("1. 구조","Actor/Component와 Skeletal Mesh/Skeleton으로 최소 캐릭터 구성"),("2. 큰 변형","Morph Target과 Animation Blueprint로 압축·늘어남·착지 반응"),("3. 표면","Material, Instance, UV/Mask로 젤리·먼지·젖음 구분"),("4. 부착·효과","Socket, 제한된 Chaos, Niagara로 큰 조각과 짧은 효과"),("5. 판정","Collision과 Blueprint 상태를 화면 변화와 같은 시점에 연결"),("6. 온라인","핵심 상태만 Replication/RPC로 공유하고 장식은 로컬 재생"),("7. 최적화","Profiling 후 LOD/Culling/ISM/HISM/C++ 범위 결정"),("8. 고급 비교","기본 방식이 부족할 때 Substrate와 Chaos Flesh를 별도 실험")]
for a,b in steps2: line(doc,a,b)
doc.add_paragraph("판정과 표현을 분리하는 기준",style="Heading 2")
bullets(doc,["서버 판정: 질량 단계, 변장 종류, 충돌 상태, 부착 단계", "화면 표현: 모프 값, 머티리얼 값, 잔떨림, Niagara 입자", "공유 데이터: 상태 ID, 0~1 강도, 시작 시점, 난수 시드처럼 작고 재현 가능한 값", "금지할 설계: 입자 하나하나나 모든 꼭짓점 변형 결과를 네트워크로 전송"])
doc.add_paragraph("공식 참고 자료",style="Heading 2")
refs=[
"Blueprints — https://dev.epicgames.com/documentation/en-us/unreal-engine/introduction-to-blueprints-visual-scripting-in-unreal-engine",
"Skeletal Mesh — https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-assets-in-unreal-engine",
"Morph Target — https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-morph-target-pipeline-in-unreal-engine",
"Animation Blueprint — https://dev.epicgames.com/documentation/unreal-engine/animation-blueprints-in-unreal-engine",
"Niagara — https://dev.epicgames.com/documentation/unreal-engine/overview-of-niagara-effects-for-unreal-engine",
"Networking — https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine",
"Chaos Flesh — https://dev.epicgames.com/documentation/unreal-engine/chaos-flesh-overview",
"Substrate — https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine",
"Instanced Static Mesh — https://dev.epicgames.com/documentation/unreal-engine/instanced-static-mesh-component-in-unreal-engine"]
bullets(doc,refs)
doc.add_paragraph("캡처 안내",style="Heading 2"); doc.add_paragraph("화면 캡처는 실제 JellyGame 프로젝트를 Unreal Engine 5.8.4에서 연 상태로 촬영했다. 엔진 버전, 언어, 레이아웃에 따라 메뉴 이름과 위치가 조금 달라질 수 있다.")
doc.core_properties.title="언리얼 기능 상세 정의와 사용 가이드"; doc.core_properties.author="JellyGame 프로젝트"; doc.core_properties.subject="UE 5.8.4 입문자용 기능별 정의·위치·사용법"
doc.save(OUT)
print(OUT)
