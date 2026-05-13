from __future__ import annotations

import argparse
from importlib.util import find_spec
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

# Runtime dependencies used directly by this application.
RUNTIME_PACKAGES = [
    "numpy",
    "sounddevice",
    "soundfile",
    "SpeechRecognition",
    "pyttsx3",
]
POCKETSPHINX_PACKAGE = "pocketsphinx"

# Optional packages used for local development and testing.
TEST_PACKAGES = [
    "pytest",
    "pyright[nodejs]",
]


def run_pip_install(packages: Iterable[str], upgrade: bool = False) -> None:
    command = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        command.append("--upgrade")
    command.extend(packages)

    print("Running:", " ".join(command))
    subprocess.check_call(command)


def _find_conda_executable() -> str | None:
    conda_path = shutil.which("conda")
    if conda_path:
        return conda_path

    conda_from_env = os.environ.get("CONDA_EXE")
    if conda_from_env and Path(conda_from_env).exists():
        return conda_from_env

    home = Path.home()
    candidates = [
        home / "miniconda3" / "Scripts" / "conda.exe",
        home / "anaconda3" / "Scripts" / "conda.exe",
        home / "Miniconda3" / "Scripts" / "conda.exe",
        home / "Anaconda3" / "Scripts" / "conda.exe",
        home / "miniconda3" / "condabin" / "conda.bat",
        home / "anaconda3" / "condabin" / "conda.bat",
    ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def install_pocketsphinx_with_conda() -> None:
    conda_path = _find_conda_executable()
    if conda_path is None:
        raise RuntimeError(
            "Conda was not found in PATH or common install locations. "
            "Install Miniconda/Anaconda first, or add conda to PATH."
        )

    command = [conda_path, "install", "-c", "conda-forge", "pocketsphinx", "-y"]
    print("Running:", " ".join(command))
    subprocess.check_call(command)


def install_pocketsphinx() -> None:
    if find_spec("pocketsphinx") is not None:
        print("pocketsphinx is already available in the current Python environment.")
        return

    try:
        run_pip_install([POCKETSPHINX_PACKAGE])
        if find_spec("pocketsphinx") is not None:
            return
        raise RuntimeError("pocketsphinx installation completed but module is unavailable in current environment.")
        return
    except subprocess.CalledProcessError:
        print("pip install pocketsphinx failed. Trying conda-forge fallback...")

    install_pocketsphinx_with_conda()
    if find_spec("pocketsphinx") is None:
        raise RuntimeError(
            "pocketsphinx may have been installed in conda, but not in the current Python environment. "
            "If you use .venv to run app.py, install Visual C++ Build Tools and run install.py again."
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install required Python packages for conversation_with_ai."
    )
    parser.add_argument(
        "--with-test",
        action="store_true",
        help="Also install test dependencies (pytest, pyright).",
    )
    parser.add_argument(
        "--upgrade-pip",
        action="store_true",
        help="Upgrade pip before installing dependencies.",
    )
    parser.add_argument(
        "--with-pocketsphinx-conda",
        action="store_true",
        help="Force installing pocketsphinx using conda-forge.",
    )
    args = parser.parse_args()

    try:
        if args.upgrade_pip:
            run_pip_install(["pip"], upgrade=True)

        run_pip_install(RUNTIME_PACKAGES)

        if args.with_pocketsphinx_conda:
            install_pocketsphinx_with_conda()
        else:
            install_pocketsphinx()

        if args.with_test:
            run_pip_install(TEST_PACKAGES)

        print("Dependency installation completed successfully.")
        return 0
    except RuntimeError as exc:
        print(str(exc))
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Installation failed with exit code {exc.returncode}.")
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
