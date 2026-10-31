import os
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from google.adk.cli.dev_server import DevServer
from google.adk.cli.api_server import ApiServer

PLANOS_DIR = (Path(__file__).parent / "planos").resolve()

# Registra a rota de download no DevServer e ApiServer do ADK
_orig_dev_get_fast_api_app = DevServer.get_fast_api_app
_orig_api_get_fast_api_app = ApiServer.get_fast_api_app


def _add_download_route(app):
    @app.api_route("/download/{filename}", methods=["GET", "HEAD"])
    async def download_file(filename: str):
        file_path = (PLANOS_DIR / filename).resolve()
        if not file_path.is_relative_to(PLANOS_DIR) or not file_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return app


def _custom_dev_get_fast_api_app(self, **kwargs):
    app = _orig_dev_get_fast_api_app(self, **kwargs)
    return _add_download_route(app)


def _custom_api_get_fast_api_app(self, **kwargs):
    app = _orig_api_get_fast_api_app(self, **kwargs)
    return _add_download_route(app)


DevServer.get_fast_api_app = _custom_dev_get_fast_api_app
ApiServer.get_fast_api_app = _custom_api_get_fast_api_app
