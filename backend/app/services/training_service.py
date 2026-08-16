"""Service that triggers the training pipeline safely as a subprocess."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings
from ..utils.errors import ForbiddenError

_retrain_state = {
    "running": False,
    "started_at": None,
    "completed_at": None,
    "message": "",
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _training_command() -> list[str]:
    """Build the command to run the training pipeline.

    Prefers the venv Python so TensorFlow resolves correctly.
    """
    venv_python = Path(settings.MODEL_PATH).parent.parent / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    if venv_python.exists():
        python = str(venv_python)
    else:
        python = sys.executable

    script = Path(__file__).resolve().parent.parent.parent / "training" / "train.py"
    return [python, str(script), "--no-plots"]


class TrainingService:
    @property
    def running(self) -> bool:
        return _retrain_state["running"]

    def status(self) -> dict:
        state = _retrain_state
        if state["running"]:
            status = "running"
        elif state["completed_at"]:
            status = "completed"
        else:
            status = "idle"
        return {
            "status": status,
            "running": state["running"],
            "started_at": state["started_at"],
            "completed_at": state["completed_at"],
            "current_epoch": None,
            "total_epochs": None,
            "message": state["message"],
        }

    def trigger(self, environment: str, allow_retrain: bool) -> dict:
        if not allow_retrain or environment not in ("development", "local", "test"):
            raise ForbiddenError(
                "Retraining is disabled in this environment. Set ALLOW_RETRAIN=true "
                "and ENVIRONMENT=development to retrain locally."
            )
        if _retrain_state["running"]:
            return {
                "status": "already_running",
                "message": "A retraining job is already in progress.",
            }

        command = _training_command()
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        _retrain_state.update(
            running=True,
            started_at=_utcnow(),
            completed_at=None,
            message="Training in progress…",
        )

        # Reap asynchronously so we never block the API.
        def _reap() -> None:
            try:
                proc.wait()
            finally:
                _retrain_state["running"] = False
                _retrain_state["completed_at"] = _utcnow()
                _retrain_state["message"] = (
                    "Training completed. The model was replaced with the new weights."
                    if proc.returncode == 0
                    else "Training failed. Check the API logs for details."
                )

        threading.Thread(target=_reap, daemon=True).start()

        return {
            "status": "started",
            "message": "Retraining started. Poll /api/training/status for progress.",
        }
