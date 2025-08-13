import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    base_url: str
    token: str | None
    api_version: str


def load_settings() -> Settings:
    load_dotenv()
    base_url = os.getenv("BASE_URL", "https://api.github.com")
    token = os.getenv("GITHUB_TOKEN")
    api_version = os.getenv("GITHUB_API_VERSION", "2022-11-28")
    return Settings(base_url=base_url, token=token, api_version=api_version)
