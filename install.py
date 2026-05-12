from __future__ import annotations

import argparse
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

# Optional packages used for local development and testing.
TEST_PACKAGES = [
    "pytest",
]


def run_pip_install(packages: Iterable[str], upgrade: bool = False) -> None:
    command = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        command.append("--upgrade")
    command.extend(packages)

    print("Running:", " ".join(command))
    subprocess.check_call(command)


def install_pocketsphinx_with_conda() -> None:
    conda_path = shutil.which("conda")
    if conda_path is None:
        raise RuntimeError(
            "Conda was not found in PATH. Install Miniconda/Anaconda first, then try again."
        )

    command = [conda_path, "install", "-c", "conda-forge", "pocketsphinx", "-y"]
    print("Running:", " ".join(command))
    subprocess.check_call(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install required Python packages for conversation_with_ai."
    )
    parser.add_argument(
        "--with-test",
        action="store_true",
        help="Also install test dependencies (pytest).",
    )
    parser.add_argument(
        "--upgrade-pip",
        action="store_true",
        help="Upgrade pip before installing dependencies.",
    )
    parser.add_argument(
        "--with-pocketsphinx-conda",
        action="store_true",
        help="Install pocketsphinx using conda-forge (recommended on Windows).",
    )
    args = parser.parse_args()

    try:
        if args.upgrade_pip:
            run_pip_install(["pip"], upgrade=True)

        run_pip_install(RUNTIME_PACKAGES)

        if args.with_test:
            run_pip_install(TEST_PACKAGES)

        if args.with_pocketsphinx_conda:
            install_pocketsphinx_with_conda()

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
