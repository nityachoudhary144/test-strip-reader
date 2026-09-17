from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "design.md"
OUTPUT = HERE / "diagrams"

MERMAID_BLOCK = re.compile(r"^```mermaid\n(.*?)^```", re.S | re.M)
HEADING = re.compile(r"^#{2,4} (.+)$", re.M)

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def diagrams(markdown: str) -> list[tuple[str, str]]:
    found = []
    for index, match in enumerate(MERMAID_BLOCK.finditer(markdown), start=1):
        headings = HEADING.findall(markdown[: match.start()])
        title = headings[-1] if headings else f"diagram {index}"
        found.append((f"{index:02d}-{slug(title)}", match.group(1)))
    return found


def puppeteer_config(workdir: Path) -> Path | None:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            config = workdir / "puppeteer.json"
            config.write_text(
                json.dumps({"executablePath": candidate}), encoding="utf-8"
            )
            return config
    return None


def render(name: str, source: str, config: Path | None, workdir: Path) -> Path:
    mmd = workdir / f"{name}.mmd"
    mmd.write_text(source, encoding="utf-8")

    target = OUTPUT / f"{name}.png"
    command = [
        "npx",
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(mmd),
        "-o",
        str(target),
        "-b",
        "white",
        "-s",
        "2",
    ]
    if config is not None:
        command += ["-p", str(config)]

    subprocess.run(command, check=True, capture_output=True)
    return target


def main() -> int:
    if shutil.which("npx") is None:
        print("npx not found, so the diagrams cannot be rendered")
        return 1

    found = diagrams(SOURCE.read_text(encoding="utf-8"))
    if not found:
        print(f"no mermaid blocks found in {SOURCE}")
        return 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        config = puppeteer_config(workdir)
        for name, source in found:
            print(f"rendering {name}")
            render(name, source, config, workdir)

    print(f"wrote {len(found)} diagrams to {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
