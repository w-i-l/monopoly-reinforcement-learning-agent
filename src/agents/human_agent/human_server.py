from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

class HumanServer:
    def __init__(self, server_port: int = 6060, frontend_port: int = 6061):
        self.app = FastAPI(title="Monopoly Game API")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[f"http://127.0.0.1:{frontend_port}", f"http://127.0.0.1:{server_port}"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )