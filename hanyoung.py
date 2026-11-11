"""한/영 잘못 친 텍스트 고치기: 블럭 지정 -> 한/영 키 -> 변환.  sksms <-> 나는

  Windows: 한/영 키.  Mac: Caps Lock (입력 소스 전환 키로 쓰는 경우).
  설치: pip install pynput pyperclip
  실행: python hanyoung.py   (Windows 백그라운드: pythonw hanyoung.py)
  Mac: 실행하는 터미널 앱에 '손쉬운 사용' + '입력 모니터링' 권한 필요.
  테스트: python hanyoung.py --test
  로그: 임시 폴더의 hanyoung.log (선택한 텍스트 내용은 기록 안 함)
"""
import logging
import os
import sys
import tempfile
import threading
import time

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = [""] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")
KEY2JAMO = dict(zip("qwertyuiopasdfghjklzxcvbnmQWERTOP",
                    "ㅂㅈㄷㄱㅅㅛㅕㅑㅐㅔㅁㄴㅇㄹㅎㅗㅓㅏㅣㅋㅌㅊㅍㅠㅜㅡㅃㅉㄸㄲㅆㅒㅖ"))
JAMO2KEY = {v: k for k, v in KEY2JAMO.items()}
COMBINE = {"ㅗㅏ": "ㅘ", "ㅗㅐ": "ㅙ", "ㅗㅣ": "ㅚ", "ㅜㅓ": "ㅝ", "ㅜㅔ": "ㅞ", "ㅜㅣ": "ㅟ", "ㅡㅣ": "ㅢ",
           "ㄱㅅ": "ㄳ", "ㄴㅈ": "ㄵ", "ㄴㅎ": "ㄶ", "ㄹㄱ": "ㄺ", "ㄹㅁ": "ㄻ", "ㄹㅂ": "ㄼ",
           "ㄹㅅ": "ㄽ", "ㄹㅌ": "ㄾ", "ㄹㅍ": "ㄿ", "ㄹㅎ": "ㅀ", "ㅂㅅ": "ㅄ"}
SPLIT = {v: k for k, v in COMBINE.items()}
# ponytail: Ctrl+Insert가 안 먹는 앱만 등록. 다른 앱도 안 되면 로그의 app= 이름을 여기 추가
CTRL_CV_APPS = {"kakaotalk.exe"}


def to_korean(text):
    # 대문자는 Caps Lock으로 친 경우라 소문자 자모로 (Shift 쌍자음 QWERTOP 제외)
    j = [KEY2JAMO.get(c) or KEY2JAMO.get(c.lower(), c) for c in text]
    out, i, n = [], 0, len(j)

    def vowel_at(k):
        return k < n and j[k] in JUNG

    while i < n:
        c = j[i]
        if c in CHO and vowel_at(i + 1):
            v = j[i + 1]
            i += 2
            if i < n and v + j[i] in COMBINE:
                v = COMBINE[v + j[i]]
                i += 1
            t = ""
            # 받침 후보 뒤에 모음이 오면 다음 글자 초성으로 넘김
            if i < n and j[i] in JONG and not vowel_at(i + 1):
                t = j[i]
                i += 1
                if i < n and t + j[i] in COMBINE and not vowel_at(i + 1):
                    t = COMBINE[t + j[i]]
                    i += 1
            out.append(chr(0xAC00 + (CHO.index(c) * 21 + JUNG.index(v)) * 28 + JONG.index(t)))
        else:
            # ponytail: 낱자음 겹받침(rt -> ㄳ)은 안 합침, 필요하면 여기서 COMBINE
            if c in JUNG and i + 1 < n and c + j[i + 1] in COMBINE:
                c = COMBINE[c + j[i + 1]]
                i += 1
            out.append(c)
            i += 1
    return "".join(out)


def to_english(text):
    out = []
    for c in text:
        code = ord(c) - 0xAC00
        parts = [CHO[code // 588], JUNG[code // 28 % 21], JONG[code % 28]] if 0 <= code < 11172 else [c]
        for p in parts:
            out.extend(JAMO2KEY.get(q, q) for q in SPLIT.get(p, p))
    return "".join(out)


def convert(text):
    has_ko = any("가" <= c <= "힣" or "ㄱ" <= c <= "ㅣ" for c in text)
    return to_english(text) if has_ko else to_korean(text)


def test():
    cases = {"sksms": "나는", "dkssudgktpdy": "안녕하세요", "ekfrdl": "닭이", "rkqt": "값",
             "dhks": "완", "dmlwk": "의자", "dkswdk": "앉아", "Rhcl": "꼬치", "SKSMS": "나는",
             "gksrmf 123!": "한글 123!"}
    for en, ko in cases.items():
        assert convert(en) == ko, (en, convert(en), ko)
        if en.islower() or not en.isalpha():
            assert convert(ko) == en, (ko, convert(ko), en)
    assert convert("ㅋㅋ") == "zz"
    already_running()
    assert already_running()
    print("ok")


def already_running():
    # 포트 bind는 Hyper-V/Docker 예약 범위에 걸리면 실패해서 OS 락 사용. 프로세스가 끝나면 OS가 풀어줌
    if sys.platform == "darwin":
        import fcntl
        fd = os.open(os.path.join(tempfile.gettempdir(), "hanyoung.lock"), os.O_CREAT | os.O_WRONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except OSError:
            return True
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW(None, False, "hanyoung-single-instance")
    return ctypes.get_last_error() == 183  # ERROR_ALREADY_EXISTS


def exe_of(hwnd):
    import ctypes
    from ctypes import wintypes as w
    user32, kernel32 = ctypes.WinDLL("user32"), ctypes.WinDLL("kernel32")
    user32.GetWindowThreadProcessId.argtypes = (w.HWND, ctypes.POINTER(w.DWORD))
    kernel32.OpenProcess.restype = w.HANDLE
    kernel32.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
    kernel32.QueryFullProcessImageNameW.argtypes = (w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD))
    kernel32.CloseHandle.argtypes = (w.HANDLE,)
    pid = w.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    buf, size = ctypes.create_unicode_buffer(1024), w.DWORD(1024)
    kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(handle)
    return os.path.basename(buf.value).lower()


def foreground_app():
    if sys.platform == "darwin":
        return ""
    import ctypes
    from ctypes import wintypes as w
    user32 = ctypes.WinDLL("user32")
    user32.GetForegroundWindow.restype = w.HWND
    return exe_of(user32.GetForegroundWindow())


def clipboard_owner():
    import ctypes
    from ctypes import wintypes as w
    user32 = ctypes.WinDLL("user32")
    user32.GetClipboardOwner.restype = w.HWND
    hwnd = user32.GetClipboardOwner()
    return exe_of(hwnd) if hwnd else "NULL"


def main():
    import pyperclip
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode

    # 중복 실행 방지: 두 개 돌면 연달아 변환해서 원래대로 돌아감
    if already_running():
        return
    # 창 없는 exe라 로그가 유일한 진단 수단
    logging.basicConfig(filename=os.path.join(tempfile.gettempdir(), "hanyoung.log"), filemode="w",
                        level=logging.INFO, format="%(asctime)s %(message)s", encoding="utf-8")
    threading.excepthook = lambda a: logging.error("실패", exc_info=(a.exc_type, a.exc_value, a.exc_traceback))

    mac = sys.platform == "darwin"
    kb = keyboard.Controller()
    # Windows 기본은 Ctrl+Insert: 터미널에서 선택 없이 Ctrl+C면 입력/실행 중인 게 날아감
    default_keys = (((Key.cmd, KeyCode.from_vk(8)), (Key.cmd, KeyCode.from_vk(9))) if mac
                    else ((Key.ctrl, Key.insert), (Key.shift, Key.insert)))
    ctrl_cv = (Key.ctrl, KeyCode.from_vk(0x43)), (Key.ctrl, KeyCode.from_vk(0x56))
    copy_wait = 0.5  # 느린 앱에서 변환 안 되면 늘리기. 선택이 없을 때 클립보드가 비어 있는 시간이기도 함
    paste_wait = 0.5  # 앱이 붙여넣기를 읽기 전에 복원하면 옛 클립보드가 붙음
    last = [0.0]
    last_new = [""]
    busy = threading.Lock()

    def combo(mod, key):
        with kb.pressed(mod):
            kb.tap(key)

    def copied(app, saved):
        # 다른 프로세스가 비워진 클립보드에 옛 글자를 되써넣으면 블럭이 없어도 그 글자가 쳐짐.
        # 포그라운드 앱이 새로 쓴 글자만 선택으로 인정
        end = time.monotonic() + copy_wait
        ignored = None
        while time.monotonic() < end:
            time.sleep(0.05)
            text = pyperclip.paste()
            if text:
                owner = "" if mac else clipboard_owner()
                if text != saved and (mac or owner == app):
                    return text
                ignored = owner
        if ignored is not None:
            logging.info("ignored clipboard owner=%s app=%s", ignored, app)
        return ""

    def fix():
        app = foreground_app()
        copy, paste = ctrl_cv if app in CTRL_CV_APPS else default_keys
        # ponytail: 클립보드는 텍스트만 복원됨 (이미지 등은 날아감)
        saved = pyperclip.paste()
        try:
            pyperclip.copy("")
            combo(*copy)
            sel = copied(app, saved)
            # ponytail: 카톡은 소유자 검증으로 못 거르니 직전 결과면 무시. 같은 글을 바로 되돌리기는 안 됨
            stale = app in CTRL_CV_APPS and sel == last_new[0]
            # 선택 없으면 빈 값. VS Code·엑셀 등은 선택 없을 때 줄/셀을 개행 포함해 복사하니 무시
            new = convert(sel) if sel and not sel.endswith("\n") and not stale else sel
            logging.info("toggle app=%s selected=%d converted=%s stale=%s", app, len(sel), new != sel, stale)
            if new != sel:
                last_new[0] = new
                pyperclip.copy(new)
                combo(*paste)
                time.sleep(paste_wait)
        finally:
            pyperclip.copy(saved)

    def run_fix():
        # 연타로 겹치면 뒤 스레드가 변환 결과를 원본 클립보드로 착각해 복원함
        if busy.acquire(blocking=False):
            try:
                fix()
            finally:
                busy.release()

    def is_toggle(key):
        return key == Key.caps_lock if mac else getattr(key, "vk", None) == 0x15  # VK_HANGUL

    def on_key(key):
        if is_toggle(key) and time.monotonic() - last[0] > 0.5:
            last[0] = time.monotonic()
            threading.Thread(target=run_fix, daemon=True).start()

    # Mac Caps Lock 전환은 press/release 중 어느 쪽으로 올지 불확실 -> 둘 다 받고 0.5초 디바운스
    listener = keyboard.Listener(on_press=on_key, on_release=on_key if mac else None)
    print("실행 중. 블럭 지정 후 " + ("Caps Lock" if mac else "한/영") + ". 종료: Ctrl+C")
    if mac:
        listener.run()  # macOS 입력 소스 API는 메인 스레드에서만 안전
    else:
        listener.start()
        while listener.is_alive():
            listener.join(1)


if __name__ == "__main__":
    test() if "--test" in sys.argv else main()
