
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
CORALSCOP_DIR = ROOT / "third_party" / "coralscop"
CHECKPOINT = CORALSCOP_DIR / "checkpoints" / "vit_b_coralscop.pth"

if not CHECKPOINT.is_file():
    raise FileNotFoundError(f"Missing CoralSCOP checkpoint: {CHECKPOINT}")

app = modal.App("coral-companion-segmentation-worker")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libglib2.0-0", "libgl1", "libgomp1")
    .pip_install_from_requirements(str(ROOT / "requirements.txt"))
    .env({"PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    .add_local_dir(
        str(APP_DIR),
        remote_path="/root/app",
    )
    .add_local_dir(
        str(CORALSCOP_DIR / "segment_anything"),
        remote_path="/root/third_party/coralscop/segment_anything",
    )
    .add_local_file(
        str(CHECKPOINT),
        remote_path=(
            "/root/third_party/coralscop/checkpoints/"
            "vit_b_coralscop.pth"
        ),
    )
)

@app.function(
    image=image,
    gpu="T4",
    max_containers=1,
    timeout=600,
    startup_timeout=900,
    scaledown_window=60,
)

@modal.asgi_app(requires_proxy_auth=True)
def serve():
    from app.api.main import app as fastapi_app

    return fastapi_app
