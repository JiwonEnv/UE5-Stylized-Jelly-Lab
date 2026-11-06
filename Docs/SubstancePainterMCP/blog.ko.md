# Substance 3D Painter 9를 Codex에 MCP로 연결하기 — Windows 실전 기록

작성일: 2026년 11월 5일

Substance 3D Painter를 AI에게 말로 제어하게 만들려면 무엇이 필요할까? 이번에는 Windows에 설치된 Painter 9.0.0을 Codex에 MCP로 등록하고, 실제 프로그램에서 응답이 돌아오는 것까지 확인했다. 설치 과정에서 만난 버전 차이와 해결 방법을 함께 정리한다.

## 이번에 확인한 환경

| 항목 | 실제 사용 환경 |
|---|---|
| 운영체제 | Windows |
| Painter | Adobe Substance 3D Painter 9.0.0 |
| 외부 Python | 3.14, MCP 전용 가상환경 |
| MCP Python SDK | 1.30.0 |
| 서버 | diffdaff/substance-painter-mcp + 로컬 호환 어댑터 |
| 연결 | Codex → 표준 입출력 MCP → Painter 로컬 HTTP |
| Painter 응답의 API 버전 | JavaScript API 1.1.17 |

![실제로 실행한 Painter 9.0.0](images/01-painter.png)

*화면 1. 이번에 연결한 Painter. 오른쪽 아래에서 9.0.0 버전을 확인할 수 있다.*

## 1. Painter 버전부터 확인한다

공개 MCP 서버마다 사용하는 Painter API가 다르다. 이번 PC에는 Painter 9가 설치되어 있었기 때문에 최신 Python 레이어 API에 의존하는 플러그인을 그대로 적용하는 대신, 원격 스크립팅 방식을 선택했다.

사용한 원본은 [diffdaff의 Substance Painter MCP](https://github.com/diffdaff/substance-painter-mcp)다. 원본 설명의 테스트 대상은 Painter 10.x/11.x다. 따라서 이 글의 Painter 9 연결 결과는 아래에 소개하는 로컬 보정과 실제 검증을 포함한 결과다. 원본 그대로의 모든 기능이 Painter 9에서 동작한다는 뜻은 아니다.

이번에 받은 소스 커밋은 `23a1e3726962421d2b7412343be851f536c99747`이다.

## 2. MCP 전용 Python 환경을 만든다

Painter 안에서 실행되는 Python과 MCP 서버를 실행하는 외부 Python은 서로 다르다. 여기서는 외부 Python으로 가상환경을 만들었다. 아래 PowerShell 예시의 경로는 본인 환경에 맞게 바꾼다.

```powershell
git clone https://github.com/diffdaff/substance-painter-mcp.git C:\Tools\substance-painter-mcp
Set-Location C:\Tools\substance-painter-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install 'mcp>=1.28,<2'
```

버전 상한을 지정하는 이유가 있다. 이번 설치에서 원본의 `mcp>=1.0.0` 조건으로는 MCP 2.3.0이 설치되었고, 원본 서버의 `mcp.server.fastmcp` 가져오기가 실패했다. 1.30.0으로 맞춘 뒤 정상 실행됐다. 같은 코드를 사용할 때는 검증한 의존성 범위를 유지하는 편이 재현하기 쉽다.

이번 작업 폴더에는 실제 설치 버전을 기록한 `requirements-lock.txt`도 저장했다.

## 3. Painter를 원격 스크립팅 옵션으로 실행한다

Painter가 켜져 있다면 작업을 저장하고 종료한 다음 아래처럼 실행한다.

```powershell
Start-Process -FilePath 'C:\Program Files\Adobe\Adobe Substance 3D Painter\Adobe Substance 3D Painter.exe' -ArgumentList '--enable-remote-scripting'
```

이 설정에서는 서버가 Painter의 `localhost:60041/run.json`으로 요청을 보낸다. 실제 PC에서는 IPv6 루프백 주소 `::1`에서 수신 중인 것도 확인했다. 따라서 주소를 무조건 `127.0.0.1`로 바꾸기보다는 검증한 `localhost`를 유지했다.

Painter 실행 옵션은 프로그램을 시작할 때 적용된다. 평소처럼 실행한 Painter에서 연결이 안 된다면, 저장 후 종료하고 이 옵션을 넣어 다시 실행한다. 이번 프로젝트에는 같은 옵션으로 실행하는 `Tools/Start-PainterMCP.ps1`도 준비했다.

![원격 Python 실행 결과가 남은 Painter 로그](images/02-remote-log.png)

*화면 2. 외부에서 보낸 Python 코드가 Painter 안에서 실행되면 로그에 출력이 나타난다.*

## 4. Painter 9 호환 어댑터를 적용한다

이번 연결에서는 원본 서버와 같은 폴더에 `local_adapter.py`를 추가했다. 어댑터 파일은 이 글과 함께 제공하는 실제 작업 파일을 사용한다. 원본 저장소에는 포함되지 않은 로컬 추가 파일이다.

보정한 부분은 세 가지다.

- `check_connection`: JavaScript API로 실제 버전과 프로젝트 열림 상태를 읽도록 변경했다.
- `get_project_info`: Painter 9에서 지원되는 JavaScript API로 프로젝트 상태와 텍스처 세트를 조회하도록 변경했다.
- `create_fill_layer`: 최신 Python `layerstack` API에 의존하므로 도구 목록에서 제외했다.

원본의 연결 확인 코드는 Python `print()` 응답을 버전으로 사용하고 있었다. 실제 테스트에서 Python 출력은 Painter 로그에 나타나고 HTTP 응답은 `null`이었다. 그래서 버전 조회는 값을 반환할 수 있는 JavaScript 표현식으로 바꿨다.

연결 확인은 성공했지만, 프로젝트 생성·베이킹·내보내기는 이번 검증에서 실행하지 않았다. 특히 Painter 9에서 이 작업들을 사용할 때는 별도 프로젝트로 기능별 검증이 필요하다.

## 5. Codex에 서버를 등록한다

Codex는 로컬 명령으로 실행하는 MCP 서버를 등록할 수 있다. 공식 등록 방식은 [OpenAI MCP 문서](https://developers.openai.com/codex/mcp)에서 확인할 수 있다.

어댑터를 복사한 뒤 다음처럼 등록한다.

```powershell
codex mcp add substance-painter -- 'C:\Tools\substance-painter-mcp\.venv\Scripts\python.exe' 'C:\Tools\substance-painter-mcp\local_adapter.py'
codex mcp get substance-painter
```

이번 PC에서는 실제 프로젝트 아래의 절대 경로로 등록했다. 설정 파일 위치는 `%USERPROFILE%\.codex\config.toml`이다. 직접 작성할 경우 구성은 다음 형태다.

```toml
[mcp_servers.substance-painter]
command = 'C:\Tools\substance-painter-mcp\.venv\Scripts\python.exe'
args = ['C:\Tools\substance-painter-mcp\local_adapter.py']
```

기존 설정을 통째로 덮어쓰지 않고 이 서버 항목을 추가한다. 저장된 설정을 현재 앱의 도구 목록에 반영하려면 Codex를 재시작한다. 이번 작업에서는 사용자 설정 등록과 독립 MCP 클라이언트 검증까지 완료했으며, 실행 중인 이 대화에 새 도구가 반영되는 단계는 재시작 후 확인해야 한다.

## 6. 실제 MCP 호출로 확인한다

포트가 열렸다는 사실만으로 연결 검증을 끝내지 않았다. 제공한 `verify_mcp.py`는 실제 MCP 클라이언트로 서버를 실행하고 다음 순서로 확인한다.

1. MCP 초기화
2. 도구 목록 조회
3. `check_connection` 호출
4. `get_project_info` 호출
5. `execute_script`로 Painter 로그 출력

```powershell
.\.venv\Scripts\python.exe .\verify_mcp.py
```

실제 연결 응답은 다음과 같다.

```json
{
  "connected": true,
  "version": {
    "api": "1.1.17",
    "painter": "9.0.0"
  },
  "project_open": false
}
```

`project_open: false`는 오류가 아니다. 프로그램은 연결되어 있지만 아직 프로젝트를 열지 않았다는 의미다. 프로젝트 조회 역시 다음처럼 정상 응답했다.

```json
{
  "project_open": false,
  "texture_sets": []
}
```

![MCP 경유 실행까지 확인한 Painter 로그](images/03-mcp-verified.png)

*화면 3. MCP 클라이언트에서 도구를 호출한 뒤 Painter에 남긴 검증 메시지. 설정 화면을 꾸민 이미지가 아니라 실제 프로그램 캡처다.*

도구 목록에는 프로젝트 생성·열기·저장, 텍스처 가져오기, 베이킹, 내보내기, 스크립트 실행, 연결 확인, 프로젝트 정보 조회까지 9개가 나타났다. 목록에 나타나는 것과 각 기능의 실행 성공은 구분해야 한다. 이번에 실제로 확인한 범위는 연결과 조회, Python 로그 출력이다.

## 연결 후 처음 요청해 볼 내용

Codex를 재시작하고 Painter를 위 옵션으로 실행한 상태에서 다음처럼 요청하면 된다.

> Substance Painter MCP로 연결 상태와 Painter 버전을 확인해줘. 현재 프로젝트가 열려 있는지도 알려줘.

프로젝트를 연 다음에는 이렇게 이어갈 수 있다.

> 현재 Painter 프로젝트의 텍스처 세트 목록을 조회해줘.

베이킹이나 내보내기는 먼저 대상 프로젝트와 출력 경로를 정한 뒤 진행한다. 원격 스크립팅은 실행 중인 Painter를 제어하므로 로컬 연결로 유지하고, 외부에 포트를 노출할 필요는 없다.

## 연결이 안 될 때 확인할 것

| 증상 | 확인할 내용 |
|---|---|
| Painter 연결 실패 | 프로그램이 완전히 실행됐는지, 시작 옵션을 넣었는지 확인 |
| FastMCP 가져오기 오류 | 외부 가상환경에 MCP 1.x가 설치됐는지 확인 |
| 버전 값이 null로 표시 | 원본 대신 호환 어댑터를 실행하는지 확인 |
| Codex에 서버가 안 보임 | 등록 경로 확인 후 Codex 재시작 |
| 텍스처 세트가 비어 있음 | Painter에서 프로젝트를 열었는지 확인 |
| 레이어 관련 API 오류 | Painter 버전과 API 지원 범위 확인; 이 구성은 fill-layer 도구 제외 |

Painter MCP 연결에서 가장 중요한 것은 설치된 Painter 버전에 맞는 API를 선택하고, 실제 MCP 호출 결과로 확인하는 것이다. 이번 환경에서는 Painter 9.0.0의 응답과 MCP 도구 통신을 확인했으며, 다음 단계는 프로젝트를 열어 필요한 작업을 하나씩 검증하는 것이다.

## 참고 자료와 함께 제공하는 파일

- [원본 Substance Painter MCP 저장소](https://github.com/diffdaff/substance-painter-mcp)
- [Codex MCP 공식 문서](https://developers.openai.com/codex/mcp)
- [Adobe Painter Python 플러그인 공식 안내](https://experienceleague.adobe.com/en/docs/substance-3d-dev/painter-python/tutorials/create-a-python-plugin)
- 로컬 어댑터: `Tools/substance-painter-remote-mcp/local_adapter.py`
- MCP 검증 도구: `Tools/substance-painter-remote-mcp/verify_mcp.py`
- 실제 검증 결과: `Tools/substance-painter-remote-mcp/verification.json`
- 버전 기록: `Tools/substance-painter-remote-mcp/requirements-lock.txt`
- 실행 도우미: `Tools/Start-PainterMCP.ps1`

태그: SubstancePainter, MCP, Codex, Python, Windows, 게임개발, 텍스처링

다음 글: [Substance Painter 베이킹·텍스처 내보내기·UE5 머티리얼 연결](painter-to-ue5.ko.md)
