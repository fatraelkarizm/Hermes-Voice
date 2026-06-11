from __future__ import annotations

from pathlib import Path

from huggingface_hub import hf_hub_download
from openwakeword.utils import download_models


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_REPO = "0xrushi/nanowakeword-models"
MODEL_FILES = (
    "hey_hermes/hey_hermes_cnn_v1.onnx",
    "hey_hermes/hey_hermes_cnn_v1.onnx.data",
)


def main() -> int:
    download_models()
    for filename in MODEL_FILES:
        path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=filename,
            local_dir=PROJECT_ROOT / "models",
        )
        print(f"Downloaded {path}")

    print("Wake word model ready: models/hey_hermes/hey_hermes_cnn_v1.onnx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
