# hanyoung

한/영 상태를 잘못 둔 채 친 글자를 블럭 지정하고 한/영 키를 누르면 바꿔주는 프로그램입니다.

`sksms` → `나는`, `나는` → `sksms`

## 설치 (Windows)

1. [Releases](../../releases)에서 `hanyoung.exe`를 받습니다.
2. 실행합니다. 창 없이 백그라운드에서 동작합니다.
3. 부팅 때 자동 실행하려면 `Win+R` → `shell:startup` 폴더에 `hanyoung.exe` 바로가기를 넣습니다.

서명되지 않은 exe라 SmartScreen 경고가 뜨면 "추가 정보" → "실행"을 누르세요.

종료는 작업 관리자에서 `hanyoung.exe`를 끝내면 됩니다.

## 사용법

잘못 친 글자를 블럭 지정하고 한/영 키를 누릅니다.

- 선택에 한글이 있으면 영문 자판으로, 없으면 한글로 바꿉니다.
- 블럭이 없으면 평소처럼 한/영 전환만 됩니다.

## 알려진 제한

- 복사·붙여넣기는 Ctrl+Insert / Shift+Insert로 보냅니다. 터미널에서 Ctrl+C가 실행 중인 작업을 끊지 않게 하려는 것입니다. 카카오톡만 Ctrl+C/V를 씁니다.
- 줄바꿈으로 끝나는 선택은 무시합니다.
- 클립보드는 텍스트만 복원합니다. 이미지 등은 지워집니다.
- 블럭 없이 한/영을 누르면 클립보드가 최대 0.5초 비어 있습니다.
- 카카오톡에서는 방금 변환한 글을 바로 다시 되돌릴 수 없습니다.
- 진단 로그: `%TEMP%\hanyoung.log` (선택한 텍스트 내용은 기록하지 않습니다)

## 소스에서 실행·빌드

```
pip install pynput pyperclip
python hanyoung.py          # 실행
python hanyoung.py --test   # 변환 테스트
```

Windows exe:

```
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name hanyoung --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 hanyoung.py
```

macOS (테스트 안 됨, Caps Lock으로 입력 소스를 전환하는 설정 기준):

```
python3 -m PyInstaller --windowed --name hanyoung --hidden-import pynput.keyboard._darwin --hidden-import pynput.mouse._darwin hanyoung.py
```

앱에 "손쉬운 사용"과 "입력 모니터링" 권한이 필요합니다.
