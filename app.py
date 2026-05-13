from __future__ import annotations

import argparse
from importlib.util import find_spec
from pathlib import Path
import subprocess
import sys

from src.audio_input import AudioInputService
from src.audio_output import AudioOutputService
from src.config import AppConfig
from src.controller import AppController
from src.lm_studio_client import LMStudioClient
from src.speech_to_text import SpeechToTextService
from src.text_to_speech import TextToSpeechService
from src.ui import ConversationApp


MIN_PYTHON = (3, 10)
DEFAULT_AUTO_FIX_ENV = True
REQUIRED_IMPORTS = {
    "numpy": "numpy",
    "sounddevice": "sounddevice",
    "soundfile": "soundfile",
    "SpeechRecognition": "speech_recognition",
    "pyttsx3": "pyttsx3",
}
OPTIONAL_IMPORTS = {
    "pocketsphinx": "pocketsphinx",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start conversation_with_ai desktop application."
    )
    auto_fix_group = parser.add_mutually_exclusive_group()
    auto_fix_group.add_argument(
        "--auto-fix-env",
        action="store_true",
        default=DEFAULT_AUTO_FIX_ENV,
        help=(
            "Enable automatic dependency repair when required packages are missing. "
            "Default is enabled."
        ),
    )
    auto_fix_group.add_argument(
        "--no-auto-fix-env",
        action="store_false",
        dest="auto_fix_env",
        help="Disable automatic dependency repair.",
    )
    parser.add_argument(
        "--fix-only",
        action="store_true",
        help="Run environment check/repair only, then exit without starting UI.",
    )
    return parser.parse_args()


def _collect_missing_packages(package_map: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for package_name, import_name in package_map.items():
        if find_spec(import_name) is None:
            missing.append(package_name)
    return missing


def _try_auto_fix_dependencies(project_root: Path) -> None:
    install_script = project_root / "install.py"
    requirements_file = project_root / "requirements.txt"

    if install_script.exists():
        command = [sys.executable, str(install_script)]
        print(f"[ENV CHECK] 嘗試自動修復: {' '.join(command)}")
        try:
            subprocess.check_call(command)
            return
        except subprocess.CalledProcessError as exc:
            print(f"[ENV CHECK] install.py 失敗，退出碼: {exc.returncode}。改用 requirements.txt 重試。")

    if requirements_file.exists():
        command = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        print(f"[ENV CHECK] 嘗試自動修復: {' '.join(command)}")
        subprocess.check_call(command)
        return

    raise RuntimeError("找不到 install.py 與 requirements.txt，無法執行自動修復。")


def run_environment_checks(auto_fix_env: bool = False) -> None:
    print("[ENV CHECK] 開始環境檢測...")
    project_root = Path(__file__).resolve().parent

    if sys.version_info < MIN_PYTHON:
        required = ".".join(str(part) for part in MIN_PYTHON)
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise RuntimeError(
            f"Python 版本過低，需求 >= {required}，目前為 {current}。"
        )

    missing_required = _collect_missing_packages(REQUIRED_IMPORTS)
    if missing_required:
        if auto_fix_env:
            _try_auto_fix_dependencies(project_root)
            missing_required = _collect_missing_packages(REQUIRED_IMPORTS)

        if missing_required:
            joined = ", ".join(missing_required)
            hint = "請先執行 install.py 或安裝 requirements.txt 後再啟動。"
            if not auto_fix_env:
                hint += " 可移除 --no-auto-fix-env 以啟用自動修復。"
            raise RuntimeError(f"缺少必要套件: {joined}。{hint}")

    missing_optional = _collect_missing_packages(OPTIONAL_IMPORTS)
    if missing_optional:
        joined = ", ".join(missing_optional)
        print(
            f"[ENV CHECK] 提示: 可選套件未安裝: {joined}。"
            " 這不會影響主程式啟動；若要離線語音辨識可再安裝。"
        )

    config_path = project_root / "config.json"
    if not config_path.exists():
        print("[ENV CHECK] 找不到 config.json，將使用內建預設設定啟動。")

    print("[ENV CHECK] 環境檢測通過。")


def main() -> int:
    args = parse_args()

    try:
        run_environment_checks(auto_fix_env=args.auto_fix_env)
    except RuntimeError as exc:
        print(f"[ENV CHECK] 失敗: {exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"[ENV CHECK] 自動修復失敗，退出碼: {exc.returncode}")
        return 1

    if args.fix_only:
        print("[ENV CHECK] --fix-only 已完成，略過 UI 啟動。")
        return 0

    config = AppConfig.load()
    client = LMStudioClient(endpoint=config.lm_studio_endpoint, api_key=config.api_key)
    controller = AppController(
        config=config,
        lm_studio_client=client,
        audio_input=AudioInputService(),
        audio_output=AudioOutputService(),
        speech_to_text=SpeechToTextService(language=config.speech_language),
        text_to_speech=TextToSpeechService(),
    )
    app = ConversationApp(controller)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())