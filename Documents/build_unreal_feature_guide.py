from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

OUT = r"E:\Project\Unreal-Engine-5-Jelly-Game\Documents\언리얼_기능_기본_정의_가이드.docx"

def set_font(run, name="맑은 고딕", size=None, bold=None, color="000000"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)

def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)

def set_cell_border(cell, color="D9D9D9", size="6"):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = tcPr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tcPr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        el = borders.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), size)
        el.set(qn("w:color"), color)

def add_label_para(doc, label, body):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(label + "  ")
    set_font(r, size=10.5, bold=True, color="17365D")
    r = p.add_run(body)
    set_font(r, size=10.5)
    return p

def add_bullets(doc, items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Mm(7)
        p.paragraph_format.first_line_indent = Mm(-3)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.18
        r = p.add_run(item)
        set_font(r, size=10)

features = [
    {
        "title": "액터와 컴포넌트",
        "en": "Actor and Component",
        "one": "액터는 게임 세계에 놓이는 하나의 대상이고, 컴포넌트는 그 대상에 기능을 붙이는 부품이다.",
        "analogy": "액터가 조립 완성품이라면 컴포넌트는 바퀴, 몸체, 센서처럼 역할이 다른 부품이다.",
        "project": "젤리 캐릭터 액터에 스켈레탈 메시, 충돌, 이동, 소리, Niagara 컴포넌트를 조합한다. 먼지 덩어리나 과자 조각도 필요에 따라 별도 액터 또는 컴포넌트가 된다.",
        "works": ["액터는 위치, 회전, 크기를 가지며 레벨에 배치하거나 실행 중 생성할 수 있다.", "컴포넌트는 화면 표시, 충돌, 이동, 소리 같은 한 가지 책임을 맡는다.", "같은 액터 설계를 여러 번 배치하면 각각 별도 인스턴스로 동작한다."],
        "not": "액터 하나에 모든 로직을 몰아넣으면 수정과 재사용이 어려워진다. 작은 장식 하나마다 액터를 만들면 관리 비용도 커질 수 있다.",
        "first": "BP_JellyCharacter 액터를 만들고 메시, 충돌, 이동 컴포넌트를 분리해 이름을 붙인다."
    },
    {
        "title": "스태틱 메시",
        "en": "Static Mesh",
        "one": "뼈대 없이 형태가 고정된 3D 물체 자산이다.",
        "analogy": "관절이 없는 장난감 블록과 같다. 전체를 옮기거나 돌릴 수 있지만 몸 자체를 뼈로 구부리지는 않는다.",
        "project": "바닥, 가구, 단단한 과자 조각, 일반 잡동사니에 적합하다. 떨어진 부스러기는 스태틱 메시와 단순 물리를 조합할 수 있다.",
        "works": ["모델의 면과 꼭짓점, UV, 머티리얼 슬롯을 저장한다.", "충돌 모양과 LOD를 함께 설정할 수 있다.", "같은 물체가 많으면 인스턴싱으로 묶어 그릴 수 있다."],
        "not": "스태틱이라는 이름은 절대 움직이지 않는다는 뜻이 아니다. 물체 전체 이동과 물리는 가능하지만, 스켈레톤 애니메이션을 직접 쓰지 않는다는 뜻에 가깝다.",
        "first": "과자 조각 한 종류를 스태틱 메시로 가져오고 단순 충돌과 2단계 LOD를 설정한다."
    },
    {
        "title": "스켈레탈 메시",
        "en": "Skeletal Mesh",
        "one": "뼈대에 연결되어 구부러지고 움직일 수 있는 3D 메시다.",
        "analogy": "겉가죽이 내부 철사 인형을 따라 움직이는 구조다.",
        "project": "기본 젤리 몸, 먼지 외피, 접히는 휴지처럼 큰 형태 변화와 부분 움직임이 필요한 자산에 사용한다.",
        "works": ["각 꼭짓점이 어떤 뼈의 영향을 얼마나 받을지 가중치를 가진다.", "애니메이션, 모프 타깃, 물리 자산을 함께 사용할 수 있다.", "몸과 외피가 같은 스켈레톤을 공유하면 동작을 맞추기 쉽다."],
        "not": "스켈레탈 메시만 가져온다고 자연스럽게 움직이지 않는다. 스켈레톤, 스킨 가중치, 애니메이션 제어가 함께 필요하다.",
        "first": "기본 젤리와 먼지 외피가 같은 뼈 이름과 기준 자세를 쓰도록 제작 규칙을 정한다."
    },
    {
        "title": "스켈레톤과 본",
        "en": "Skeleton and Bone",
        "one": "스켈레톤은 뼈의 계층 구조이고, 본은 메시의 일부를 움직이는 기준점이다.",
        "analogy": "인형의 관절 구조와 같다. 부모 관절이 움직이면 그 아래 자식 관절도 따라간다.",
        "project": "젤리 중심, 위아래, 가장자리 보조 본을 두어 압축과 흔들림을 제어한다. 휴지 끝이나 먼지 외피 가장자리에는 제한된 보조 본을 둘 수 있다.",
        "works": ["부모와 자식 관계로 움직임을 전달한다.", "본 수와 가중치가 많을수록 표현력은 늘지만 제작과 계산 비용도 증가한다.", "소켓의 기준과 애니메이션 재사용의 기준이 된다."],
        "not": "본을 많이 넣는다고 자동으로 말랑해지지 않는다. 어떤 힘에 어떻게 반응할지는 애니메이션이나 별도 계산이 정한다.",
        "first": "큰 변형에 필요한 핵심 본과 장식용 보조 본을 구분하고, 각 본의 책임을 한 줄로 기록한다."
    },
    {
        "title": "모프 타깃",
        "en": "Morph Target or Blend Shape",
        "one": "같은 메시의 꼭짓점을 미리 만든 다른 모양으로 섞어 변형하는 기능이다.",
        "analogy": "기본 찰흙 모양과 납작한 찰흙 모양 사이를 슬라이더로 오가는 것과 같다.",
        "project": "젤리가 착지할 때 납작해짐, 좁은 틈에서 압축됨, 이동 방향으로 늘어남 같은 큰 실루엣 변화에 사용한다.",
        "works": ["보통 0에서 1 사이의 값으로 변형 강도를 조절한다.", "여러 모프 타깃을 동시에 섞을 수 있다.", "블루프린트나 애니메이션 블루프린트에서 값을 바꾼다."],
        "not": "모프 타깃은 실제 연체 물리를 계산하지 않는다. 충돌 모양도 자동으로 바뀌지 않으며, 원본과 대상 메시의 꼭짓점 구성이 맞아야 한다.",
        "first": "압축, 늘어남, 착지 납작해짐 세 가지 모프를 만들고 동시에 섞었을 때 메시가 뒤틀리지 않는지 확인한다."
    },
    {
        "title": "애니메이션 블루프린트",
        "en": "Animation Blueprint",
        "one": "스켈레탈 메시가 현재 어떤 자세와 애니메이션을 사용할지 매 프레임 결정하는 전용 블루프린트다.",
        "analogy": "배우의 움직임을 실시간으로 지시하는 무대 감독과 같다.",
        "project": "속도, 가속, 착지 충격, 방향 전환을 받아 젤리 본의 흔들림과 모프 타깃 값을 조합한다.",
        "works": ["이벤트 그래프에서 필요한 상태 값을 준비한다.", "애님 그래프에서 포즈를 섞고 최종 자세를 출력한다.", "상태 머신으로 대기, 이동, 점프 같은 상태 전환을 관리할 수 있다."],
        "not": "일반 블루프린트와 목적이 다르다. 게임 규칙 전체를 넣기보다 자세와 시각적 움직임에 집중하는 편이 좋다.",
        "first": "속도와 착지 강도만 입력받는 최소 애니메이션 블루프린트를 만들어 흔들림 강도를 확인한다."
    },
    {
        "title": "블루프린트",
        "en": "Blueprint Visual Scripting",
        "one": "코드를 직접 입력하는 대신 노드와 선을 연결해 게임 로직을 만드는 시각적 프로그래밍 시스템이다.",
        "analogy": "조건과 행동이 적힌 블록을 흐름도처럼 연결하는 방식이다.",
        "project": "변장 획득, 질량 단계 변경, 충돌 반응, 머티리얼 값 변경, Niagara 재생 같은 초기 규칙을 빠르게 시험한다.",
        "works": ["이벤트는 실행 시작점, 변수는 기억할 값, 함수는 재사용할 작업이다.", "Blueprint Class는 재사용 가능한 대상의 설계도다.", "C++로 만든 기능을 블루프린트에 노출해 함께 사용할 수 있다."],
        "not": "노드라고 해서 프로그래밍 개념이 사라지는 것은 아니다. 큰 그래프, 매 프레임 반복, 복잡한 중첩은 읽기와 성능에 부담이 될 수 있다.",
        "first": "변장 상태를 열거형으로 만들고 상태 변경 이벤트가 머티리얼과 효과를 호출하도록 작은 그래프로 구성한다."
    },
    {
        "title": "C 플러스 플러스",
        "en": "C++ Gameplay Code",
        "one": "언리얼의 핵심 시스템과 고성능 게임 로직을 작성하는 텍스트 기반 프로그래밍 방식이다.",
        "analogy": "블루프린트가 조립 가능한 제어판이라면 C++는 그 제어판에서 쓰는 부품과 내부 기계를 만드는 작업에 가깝다.",
        "project": "반복 계산의 병목, 네트워크 핵심 판정, 여러 자산에서 공통으로 쓰는 기반 기능을 측정 후 C++로 옮긴다.",
        "works": ["클래스와 컴포넌트를 만들고 블루프린트에서 쓸 함수와 변수를 공개할 수 있다.", "복잡한 데이터 구조와 엔진의 낮은 수준 기능에 접근하기 쉽다.", "컴파일 과정이 필요하며 변경 범위에 따라 대기 시간이 생긴다."],
        "not": "무조건 C++가 정답은 아니다. 빠른 실험은 블루프린트가 유리하며, 성능 문제는 측정하기 전에 단정하지 않는다.",
        "first": "프로토타입은 블루프린트로 만들고, 프로파일링에서 실제 병목으로 확인된 공통 계산만 후보로 기록한다."
    },
    {
        "title": "머티리얼",
        "en": "Material",
        "one": "3D 표면이 빛에 어떻게 보이는지 계산하는 규칙이다.",
        "analogy": "물체에 바르는 단순한 색칠이 아니라 빛을 반사하고 흡수하고 퍼뜨리는 방법을 정한 조리법이다.",
        "project": "젤리의 몸 색, 거칠기, 내부 산란, 젖음, 먼지로 가려진 영역을 표현한다. 과자와 휴지는 서로 다른 표면 규칙을 사용한다.",
        "works": ["베이스 컬러, 거칠기, 메탈릭, 노멀 같은 입력으로 표면을 정의한다.", "텍스처와 수학 노드를 조합해 위치별 차이를 만든다.", "불투명, 마스크, 반투명 같은 블렌드 방식은 비용과 결과가 다르다."],
        "not": "머티리얼은 물체의 실제 충돌이나 질량을 바꾸지 않는다. 반짝인다고 미끄러운 게임 판정이 자동으로 생기지도 않는다.",
        "first": "불투명 기반 젤리 머티리얼을 먼저 만들고 몸 색, 거칠기, 산란 강도를 매개변수로 노출한다."
    },
    {
        "title": "머티리얼 인스턴스",
        "en": "Material Instance and Dynamic Material Instance",
        "one": "기본 머티리얼의 구조는 유지하고 노출된 값만 빠르게 바꾸는 파생 자산 또는 실행 중 객체다.",
        "analogy": "같은 레시피로 색과 양념 비율만 바꾼 여러 메뉴를 만드는 방식이다.",
        "project": "젤리 색상별 변형, 먼지량, 젖음 정도, 노출 면적을 개별 캐릭터마다 조절한다.",
        "works": ["일반 머티리얼 인스턴스는 에디터에서 미리 값을 저장한다.", "다이내믹 머티리얼 인스턴스는 게임 실행 중 값을 바꾼다.", "스칼라 값, 색상, 텍스처 등을 매개변수로 제어한다."],
        "not": "인스턴스에서 기본 머티리얼의 노드 구조 자체를 자유롭게 다시 설계하는 것은 아니다. 구조가 달라야 하면 별도 머티리얼이나 정적 스위치를 검토한다.",
        "first": "젖음과 먼지량을 0에서 1로 바꾸는 다이내믹 인스턴스를 캐릭터 시작 시 한 번 생성해 재사용한다."
    },
    {
        "title": "UV와 마스크",
        "en": "UV and Mask",
        "one": "UV는 3D 표면을 2D 이미지에 대응시키는 좌표이고, 마스크는 효과를 적용할 영역을 흑백 또는 수치로 구분한 데이터다.",
        "analogy": "UV는 지구본을 펼친 지도이고, 마스크는 지도에서 특정 지역만 칠한 선택 영역이다.",
        "project": "젖은 위치, 먼지가 붙은 위치, 젤리가 드러난 위치를 표면별로 제어한다.",
        "works": ["UV를 통해 텍스처가 메시 표면의 어디에 놓일지 정한다.", "마스크 값 0은 적용하지 않음, 1은 완전 적용처럼 사용할 수 있다.", "여러 정보를 한 텍스처의 색상 채널에 나눠 저장할 수 있다."],
        "not": "UV 이음새에서는 마스크가 끊겨 보일 수 있다. 고해상도 마스크를 계속 네트워크로 보내는 방식은 비용이 크므로 재현 규칙을 따로 설계한다.",
        "first": "몸의 눈에 잘 띄지 않는 곳에 UV 이음새를 두고, 젖음 마스크가 이음새를 넘을 때 끊기지 않는지 시험한다."
    },
    {
        "title": "Substrate",
        "en": "Substrate Materials",
        "one": "여러 재질 층과 빛 반응을 더 유연하게 구성하기 위한 언리얼의 머티리얼 프레임워크다.",
        "analogy": "표면 하나를 단일 페인트로 보는 대신 젤리, 물막, 먼지층처럼 겹친 층으로 설계하는 방식이다.",
        "project": "젤리 위에 젖음이나 오염이 겹치는 표현을 비교 실험할 때 후보가 된다.",
        "works": ["서로 다른 표면 성질을 혼합하거나 층으로 구성한다.", "복잡한 재질 모델을 표현할 수 있지만 설정과 비용도 함께 검토해야 한다.", "프로젝트의 렌더링 설정과 목표 플랫폼에 맞춰 채택 여부를 결정한다."],
        "not": "Substrate를 쓴다고 자동으로 사실적인 결과가 나오지 않는다. 기본 머티리얼로 충분한지 먼저 비교하고 프로젝트 버전에서의 지원 상태를 확인한다.",
        "first": "같은 젤리 장면에서 기본 머티리얼과 Substrate 후보를 나란히 두고 품질과 GPU 비용을 비교한다."
    },
    {
        "title": "Niagara",
        "en": "Niagara Visual Effects",
        "one": "많은 작은 입자와 시각 효과를 규칙에 따라 생성하고 움직이는 언리얼의 VFX 시스템이다.",
        "analogy": "한 명씩 직접 배치하지 않고 분사기와 행동 규칙으로 수많은 종이 조각을 날리는 장치와 같다.",
        "project": "먼지 이탈, 물방울 비산, 짧은 충돌 효과, 젖은 이동 흔적을 표현한다.",
        "works": ["System은 전체 효과, Emitter는 입자 발생 단위, Module은 행동 규칙, Parameter는 외부 입력값이다.", "블루프린트에서 위치, 색, 강도, 시작 시점을 전달할 수 있다.", "CPU 또는 GPU 시뮬레이션을 상황에 맞게 선택한다."],
        "not": "Niagara 입자는 기본적으로 장식 표현이다. 각 입자를 승패 판정이나 정확한 물리 결과로 사용하면 동기화와 성능 문제가 커진다.",
        "first": "먼지 이탈 효과 하나를 만들고 입자 수, 수명, 발생 강도를 매개변수로 노출한다."
    },
    {
        "title": "충돌",
        "en": "Collision",
        "one": "게임 속 대상이 서로 닿았는지, 막히는지, 통과하는지를 판단하는 규칙과 형태다.",
        "analogy": "보이는 외형 주위에 설치한 보이지 않는 안전 울타리와 같다.",
        "project": "젤리 이동, 틈 통과, 물체 끌기, 부착물 손실 조건을 판정한다. 시각적 변형과 충돌 형태 변경은 함께 설계한다.",
        "works": ["단순 도형이나 메시 기반 형태로 충돌 범위를 만든다.", "Block은 막고, Overlap은 겹침을 알리며, Ignore는 무시한다.", "채널과 프리셋으로 대상 종류별 반응을 정한다."],
        "not": "눈에 보이는 메시와 충돌은 별도다. 모프 타깃으로 몸이 납작해져도 충돌이 자동으로 같은 모양이 되는 것은 아니다.",
        "first": "기본, 압축, 납작 상태마다 필요한 충돌 크기를 정의하고 상태 전환 시 화면과 판정이 어긋나지 않는지 확인한다."
    },
    {
        "title": "Chaos 물리",
        "en": "Chaos Physics",
        "one": "언리얼에서 강체, 파괴, 천 등 물리 현상을 계산하는 물리 시스템 계열이다.",
        "analogy": "게임 세계에서 중력, 충돌, 튕김 같은 규칙을 계산하는 실험실이다.",
        "project": "떨어진 과자 조각, 제한된 부착물 회전, 필요한 경우 휴지 끝의 보조 움직임을 구현할 때 사용한다.",
        "works": ["질량, 중력, 충돌, 제약 조건으로 물체 움직임을 계산한다.", "물리 자산으로 스켈레탈 메시의 충돌 몸체와 관절 제한을 정의할 수 있다.", "결과의 안정성과 비용은 물체 수와 설정에 크게 좌우된다."],
        "not": "물리를 켜는 것만으로 원하는 연출이 나오지 않는다. 조작 캐릭터 전체를 무제한 물리에 맡기면 입력 반응과 네트워크 안정성이 나빠질 수 있다.",
        "first": "큰 과자 조각 한 개에만 제한된 물리와 회전 범위를 적용하고 나머지는 애니메이션으로 처리한다."
    },
    {
        "title": "Chaos Flesh",
        "en": "Chaos Flesh",
        "one": "부피를 가진 연한 물체의 변형을 시뮬레이션하기 위한 언리얼의 변형체 기능이다.",
        "analogy": "겉면만 흔드는 대신 내부에 말랑한 구조가 있다고 보고 눌림을 계산하는 방식이다.",
        "project": "젤리 몸 전체의 실제 연체 시뮬레이션 후보지만, 첫 프로토타입의 기본 해법이 아니라 비교 실험 대상으로 둔다.",
        "works": ["저해상도 시뮬레이션 결과를 고해상도 표면 표현에 연결하는 구성을 사용할 수 있다.", "충돌과 변형을 물리적으로 계산하므로 단순 모프보다 설정과 계산 비용이 크다.", "엔진 버전과 기능 성숙도, 목표 플랫폼을 함께 확인해야 한다."],
        "not": "온라인 캐릭터의 조작감과 동기화를 자동으로 해결하지 않는다. 정확한 재현이 필요한 판정은 서버 규칙과 별도로 설계한다.",
        "first": "동일한 착지 장면을 모프 방식과 Flesh 방식으로 만들고 CPU 비용, 안정성, 조작 지연을 비교한다."
    },
    {
        "title": "소켓과 부착",
        "en": "Socket and Attachment",
        "one": "소켓은 메시나 뼈대에 만든 부착 기준점이고, 부착은 다른 대상을 그 기준에 따라 따라오게 하는 관계다.",
        "analogy": "가방에 달린 고리와 그 고리에 물건을 거는 것과 같다.",
        "project": "큰 과자 조각, 먼지 덩어리, 소리 발생점, 효과 발생점을 젤리 표면의 정해진 위치에 연결한다.",
        "works": ["본을 기준으로 위치와 회전을 저장한다.", "붙은 대상은 부모의 움직임을 따라가며 상대 위치를 추가로 조절할 수 있다.", "분리 시 부착을 해제하고 물리나 Niagara 효과로 전환할 수 있다."],
        "not": "소켓은 표면 전체에 자동으로 붙이는 시스템이 아니다. 정확한 접촉 흔적이나 넓은 부착 영역은 마스크나 별도 규칙이 필요하다.",
        "first": "큰 부착물용 소켓 수를 제한하고, 이름 규칙과 사용 가능한 재료 종류를 정한다."
    },
    {
        "title": "네트워크 복제와 RPC",
        "en": "Replication and Remote Procedure Call",
        "one": "복제는 서버의 중요한 상태를 각 플레이어 화면에 전달하는 기능이고, RPC는 다른 컴퓨터에서 특정 함수를 실행하도록 요청하는 방식이다.",
        "analogy": "서버가 공식 기록부를 관리하고 각 참가자에게 필요한 변경 사항만 알려주는 구조다.",
        "project": "질량 단계, 변장 종류, 부착 단계, 중요한 손실과 씻김 시점을 서버가 확정하고 클라이언트에 전달한다.",
        "works": ["서버가 권위 있는 게임 상태를 가진다.", "복제 변수는 값의 변경을 전달하고 RPC는 요청이나 사건을 전달한다.", "각 화면은 받은 핵심 값으로 머티리얼, 애니메이션, Niagara를 재생할 수 있다."],
        "not": "액터의 복제를 켠다고 머티리얼, 애니메이션, 입자, 물리 결과가 모두 자동으로 같아지지 않는다. 무엇을 보낼지 명시해야 한다.",
        "first": "변장 상태와 패턴 난수값만 복제하고, 작은 먼지 입자는 각 클라이언트가 로컬에서 생성하도록 나눈다."
    },
    {
        "title": "ISM과 HISM",
        "en": "Instanced Static Mesh and Hierarchical Instanced Static Mesh",
        "one": "같은 스태틱 메시를 여러 번 그릴 때 하나의 묶음으로 관리해 렌더링 부담을 줄이는 기능이다.",
        "analogy": "같은 도장을 한 번 준비해 여러 위치에 찍는 방식이다.",
        "project": "반복되는 일반 먼지 덩어리, 작은 과자 조각, 배경 잡동사니를 대량 배치할 때 검토한다.",
        "works": ["각 인스턴스는 위치, 회전, 크기를 따로 가질 수 있다.", "HISM은 계층 구조를 이용해 멀리 있거나 보이지 않는 묶음을 효율적으로 제외하는 데 유리하다.", "동일 메시와 머티리얼을 공유할수록 효과가 크다."],
        "not": "각 조각이 완전히 다른 로직과 물리를 가져야 하면 인스턴싱의 장점이 줄어든다. 개별 Actor처럼 다루는 기능에도 제한이 있다.",
        "first": "배경 과자 조각 100개를 개별 액터와 ISM으로 각각 배치해 드로 콜과 관리 편의성을 비교한다."
    },
    {
        "title": "LOD와 컬링",
        "en": "Level of Detail and Culling",
        "one": "멀리 있거나 중요하지 않은 대상을 단순하게 만들거나 그리지 않아 성능을 확보하는 기능이다.",
        "analogy": "멀리 있는 글자는 세부 획 대신 큰 모양만 보여도 되는 것과 같다.",
        "project": "먼 거리의 먼지 섬유, 잔떨림, 작은 흔적, 부착 조각 수를 줄이되 변장 윤곽과 중요한 단서는 유지한다.",
        "works": ["LOD는 거리에 따라 더 단순한 메시나 효과로 바꾼다.", "컬링은 화면 밖이거나 너무 작은 대상을 그리지 않는다.", "Niagara와 애니메이션도 거리별 품질 단계를 둘 수 있다."],
        "not": "성능만 보고 핵심 단서를 없애면 게임 규칙이 달라진다. 낮은 품질에서도 변장 판독 조건이 공정해야 한다.",
        "first": "술래의 주요 관찰 거리에서 각 LOD를 캡처하고 변장 여부가 품질 설정만으로 드러나지 않는지 비교한다."
    },
    {
        "title": "프로파일링",
        "en": "Profiling",
        "one": "게임이 느려지는 원인을 CPU, GPU, 메모리, 네트워크별로 측정하는 과정이다.",
        "analogy": "몸이 피곤하다고 무작정 약을 먹지 않고 검사로 원인을 찾는 것과 같다.",
        "project": "5인 온라인, 다수의 부착물과 흔적, 반투명과 고급 조명을 함께 켠 장면에서 1080p 60fps 목표를 검증한다.",
        "works": ["에디터가 아닌 출시 설정에 가까운 실행 파일에서 측정한다.", "CPU와 GPU 시간, 메모리, 드로 콜, 네트워크 전송량을 구분한다.", "기능을 하나씩 켜고 끄며 비용 차이를 기록한다."],
        "not": "평균 FPS 하나만으로 원인을 알 수 없다. 한 장면의 좋은 결과가 전체 게임의 안정성을 보장하지도 않는다.",
        "first": "기준 장면과 최악 장면을 정하고, 변경 전후의 동일 조건 측정값을 표로 누적한다."
    },
]

doc = Document()
sec = doc.sections[0]
sec.top_margin = Mm(20)
sec.bottom_margin = Mm(18)
sec.left_margin = Mm(22)
sec.right_margin = Mm(22)

styles = doc.styles
normal = styles["Normal"]
normal.font.name = "맑은 고딕"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
normal.font.size = Pt(10.5)
normal.font.color.rgb = RGBColor(0, 0, 0)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.25

for style_name, size, before, after in [("Title", 26, 0, 14), ("Heading 1", 18, 0, 12), ("Heading 2", 12, 10, 5)]:
    st = styles[style_name]
    st.font.name = "맑은 고딕"
    st._element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_before = Pt(before)
    st.paragraph_format.space_after = Pt(after)
    st.paragraph_format.keep_with_next = True

header = sec.header.paragraphs[0]
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = header.add_run("언리얼 기능 기본 정의 가이드")
set_font(r, size=8.5, color="666666")

footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run("젤리 비대칭 멀티플레이 게임  ·  입문자용")
set_font(r, size=8, color="777777")

p = doc.add_paragraph(style="Title")
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("언리얼 기능 기본 정의 가이드")
set_font(r, size=26, bold=True)

p = doc.add_paragraph()
r = p.add_run("젤리 비주얼과 물리 구현을 이해하기 위한 입문 문서")
set_font(r, size=14, bold=True, color="17365D")
p.paragraph_format.space_after = Pt(16)

add_label_para(doc, "대상 독자", "언리얼 엔진을 처음 접하는 기획자, 아티스트, 사운드 및 제작 협업자")
add_label_para(doc, "문서 목적", "기획서에 등장하는 제작 기능을 서로 섞지 않고 하나씩 이해하도록 돕는다. 각 기능의 정의, 젤리 프로젝트에서의 역할, 주의점, 첫 제작 과제를 같은 순서로 설명한다.")
add_label_para(doc, "핵심 관점", "보이는 표현과 게임 판정은 같은 것이 아니다. 모프 타깃, 머티리얼, Niagara는 주로 화면 표현을 담당하며, 충돌과 서버 판정은 별도로 설계한다.")

doc.add_paragraph("읽는 방법", style="Heading 2")
add_bullets(doc, [
    "처음부터 모두 외울 필요는 없다. 현재 맡은 작업과 가까운 기능부터 한 장씩 읽는다.",
    "각 장은 독립적으로 읽을 수 있다. 다른 기능의 설명을 한 장 안에 합치지 않았다.",
    "‘첫 제작 과제’는 기능을 이해했는지 확인하는 최소 실습 기준이다.",
])

doc.add_paragraph("기능 목록", style="Heading 2")
table = doc.add_table(rows=1, cols=2)
table.autofit = False
table.columns[0].width = Mm(16)
table.columns[1].width = Mm(148)
hdr = table.rows[0].cells
hdr[0].text = "번호"
hdr[1].text = "기능"
for c in hdr:
    set_cell_shading(c, "17365D")
    set_cell_border(c)
    c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for rr in c.paragraphs[0].runs:
        set_font(rr, size=9, bold=True, color="FFFFFF")
for i, f in enumerate(features, 1):
    cells = table.add_row().cells
    cells[0].text = str(i)
    cells[1].text = f["title"] + "  " + f["en"]
    if i % 2 == 0:
        for c in cells:
            set_cell_shading(c, "F3F6FA")
    for c in cells:
        set_cell_border(c)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for para in c.paragraphs:
            para.paragraph_format.space_after = Pt(0)
            for rr in para.runs:
                set_font(rr, size=9)
    cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_page_break()

for idx, f in enumerate(features, 1):
    h = doc.add_paragraph(style="Heading 1")
    h.paragraph_format.page_break_before = idx > 1
    r = h.add_run(f"{idx}  {f['title']}")
    set_font(r, size=18, bold=True)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(14)
    r = p.add_run(f["en"])
    set_font(r, size=10, bold=True, color="666666")
    add_label_para(doc, "한 문장 정의", f["one"])
    add_label_para(doc, "쉽게 비유하면", f["analogy"])
    doc.add_paragraph("이 프로젝트에서의 역할", style="Heading 2")
    p = doc.add_paragraph(f["project"])
    p.paragraph_format.line_spacing = 1.3
    doc.add_paragraph("기본 작동 방식", style="Heading 2")
    add_bullets(doc, f["works"])
    doc.add_paragraph("주의할 점", style="Heading 2")
    p = doc.add_paragraph(f["not"])
    p.paragraph_format.line_spacing = 1.3
    doc.add_paragraph("첫 제작 과제", style="Heading 2")
    p = doc.add_paragraph(f["first"])
    p.paragraph_format.line_spacing = 1.3

doc.add_page_break()
doc.add_paragraph("프로젝트 적용 순서", style="Heading 1")
p = doc.add_paragraph("기능을 한꺼번에 적용하지 않고, 판정과 표현을 분리한 작은 단계로 진행한다.")
p.paragraph_format.space_after = Pt(10)
steps = [
    ("1", "기본 대상 구성", "액터와 컴포넌트, 스켈레탈 메시, 스켈레톤으로 젤리 캐릭터의 최소 구조를 만든다."),
    ("2", "큰 변형 구현", "모프 타깃과 애니메이션 블루프린트로 압축, 늘어남, 착지 반응을 만든다."),
    ("3", "표면 표현 구현", "머티리얼, 인스턴스, UV와 마스크로 젤리, 먼지, 젖음을 구분한다."),
    ("4", "부착물과 효과", "소켓과 제한된 Chaos 물리로 큰 조각을 붙이고 Niagara로 짧은 이탈 효과를 만든다."),
    ("5", "판정 연결", "블루프린트로 상태를 연결하고 충돌과 화면 변형이 같은 시점에 바뀌게 한다."),
    ("6", "온라인 검증", "복제로 핵심 상태만 공유하고 장식 효과는 각 화면에서 재생한다."),
    ("7", "최적화", "프로파일링 결과를 기준으로 LOD, 컬링, ISM과 C++ 적용 범위를 결정한다."),
    ("8", "고급 기능 비교", "기본 방식으로 목표가 부족할 때 Substrate와 Chaos Flesh를 비교 실험한다."),
]
for n, title, body in steps:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(7)
    r = p.add_run(n + "  " + title + "  ")
    set_font(r, size=10.5, bold=True, color="17365D")
    r = p.add_run(body)
    set_font(r, size=10.5)

doc.add_paragraph("용어 사용 원칙", style="Heading 2")
add_bullets(doc, [
    "‘변형’은 화면의 모양 변화, ‘판정’은 게임 규칙이 인정하는 결과로 구분한다.",
    "‘물리’는 실제 자연 현상의 완전한 재현이 아니라 게임에 필요한 계산을 뜻한다.",
    "‘복제’는 자산 파일을 복사하는 뜻이 아니라 서버와 클라이언트 사이에 상태를 동기화하는 뜻이다.",
    "‘인스턴스’는 같은 설계를 바탕으로 만들어진 개별 대상 또는 반복 렌더링 단위를 뜻하므로 문맥을 함께 확인한다.",
])

doc.add_paragraph("참고 자료", style="Heading 2")
refs = [
    "Epic Games  Introduction to Blueprints Visual Scripting in Unreal Engine",
    "Epic Games  Morph Target Previewer",
    "Epic Games  Overview of Niagara Effects for Unreal Engine",
    "Epic Games  Networking Overview for Unreal Engine",
    "Epic Games  Chaos Flesh Overview",
    "Epic Games  Overview of Substrate Materials",
    "Epic Games  Instanced Static Mesh Component",
]
urls = [
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/introduction-to-blueprints-visual-scripting-in-unreal-engine",
    "https://dev.epicgames.com/documentation/unreal-engine/morph-target-previewer",
    "https://dev.epicgames.com/documentation/unreal-engine/overview-of-niagara-effects-for-unreal-engine",
    "https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine",
    "https://dev.epicgames.com/documentation/unreal-engine/chaos-flesh-overview",
    "https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine",
    "https://dev.epicgames.com/documentation/unreal-engine/instanced-static-mesh-component-in-unreal-engine",
]
for name, url in zip(refs, urls):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(name)
    set_font(r, size=9.5, bold=True)
    p2 = doc.add_paragraph(url)
    p2.paragraph_format.left_indent = Mm(7)
    p2.paragraph_format.space_after = Pt(5)
    for rr in p2.runs:
        set_font(rr, size=8.5, color="555555")

doc.core_properties.title = "언리얼 기능 기본 정의 가이드"
doc.core_properties.subject = "젤리 비주얼과 물리 구현을 위한 입문용 기능 설명"
doc.core_properties.author = "프로젝트 제작팀"
doc.core_properties.keywords = "Unreal Engine, 모프 타깃, 블루프린트, Niagara, 젤리 게임"
doc.save(OUT)
print(OUT)
