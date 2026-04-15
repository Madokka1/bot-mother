from __future__ import annotations

import asyncio
import os
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx
from gradio_client import Client, handle_file


@dataclass(frozen=True)
class GenerationParams:
    strength: float
    steps: int
    seed: int


class HFSpaceGenerator:
    def __init__(
        self,
        space_id: str,
        hf_token: Optional[str],
        timeout_sec: int,
        default_strength: float,
        default_steps: int,
    ) -> None:
        self._space_id = space_id
        self._hf_token = hf_token
        self._timeout_sec = timeout_sec
        self._default_strength = default_strength
        self._default_steps = default_steps
        self._client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            # gradio_client is sync; we keep one client instance per process
            self._client = Client(self._space_id, hf_token=self._hf_token)
        return self._client

    async def generate_img2img(
        self,
        init_image_path: str,
        prompt: str,
        params: GenerationParams | None = None,
    ) -> str:
        params = params or GenerationParams(
            strength=self._default_strength,
            steps=self._default_steps,
            seed=random.randint(1, 2_000_000_000),
        )

        return await asyncio.wait_for(
            asyncio.to_thread(self._predict_sync, init_image_path, prompt, params),
            timeout=self._timeout_sec,
        )

    def _predict_sync(self, init_image_path: str, prompt: str, params: GenerationParams) -> str:
        client = self._get_client()

        # Most common for Spaces built with gr.Blocks and `fn=predict`.
        api_names_to_try = ["/predict", "predict"]

        last_error: Exception | None = None
        for api_name in api_names_to_try:
            try:
                result = client.predict(
                    handle_file(init_image_path),
                    prompt,
                    float(params.strength),
                    int(params.steps),
                    int(params.seed),
                    api_name=api_name,
                )
                return self._materialize_result(result)
            except Exception as e:
                last_error = e

        # Fallback: discover API schema and use the first available endpoint.
        try:
            api = client.view_api()
            named_endpoints = list((api or {}).get("named_endpoints", {}).keys())
            for api_name in named_endpoints:
                try:
                    result = client.predict(
                        handle_file(init_image_path),
                        prompt,
                        float(params.strength),
                        int(params.steps),
                        int(params.seed),
                        api_name=api_name,
                    )
                    return self._materialize_result(result)
                except Exception as e:
                    last_error = e
        except Exception as e:
            last_error = e

        raise RuntimeError(f"HF Space predict failed: {last_error}") from last_error

    def _materialize_result(self, result: Any) -> str:
        # Common cases:
        # - str (local path or url)
        # - dict with "path"/"url"
        # - list/tuple where the first element is a path/url/dict
        if isinstance(result, (list, tuple)) and result:
            return self._materialize_result(result[0])

        if isinstance(result, dict):
            for key in ("path", "filepath", "file", "url"):
                if key in result and result[key]:
                    return self._materialize_result(result[key])

        if isinstance(result, str):
            if result.startswith("http://") or result.startswith("https://"):
                return self._download_to_tmp(result)
            if os.path.exists(result):
                return result
            # Sometimes gradio returns relative paths
            p = Path(result)
            if p.exists():
                return str(p)

        raise RuntimeError(f"Unexpected Space result: {type(result).__name__}")

    def _download_to_tmp(self, url: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp_path = tmp.name

        # sync download (inside thread)
        with httpx.Client(follow_redirects=True, timeout=60.0) as client:
            r = client.get(url)
            r.raise_for_status()
            Path(tmp_path).write_bytes(r.content)
        return tmp_path
