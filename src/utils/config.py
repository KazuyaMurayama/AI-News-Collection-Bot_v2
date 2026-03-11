"""設定管理（シングルトン・バリデーション）"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _find_project_root() -> Path:
    """プロジェクトルートを自動探索する。"""
    env_root = os.environ.get("APP_ROOT")
    if env_root:
        return Path(env_root)

    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "config.yaml").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return Path.cwd()


def load_config(config_path: str | None = None) -> dict:
    """config.yamlを読み込む。"""
    if config_path is None:
        config_path = str(_find_project_root() / "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_env(env_path: str | None = None) -> None:
    """.envを読み込む。"""
    if env_path is None:
        env_path = str(_find_project_root() / ".env")
    load_dotenv(env_path)


def validate_config(config: dict) -> list[str]:
    """設定のバリデーション。エラーメッセージのリストを返す。"""
    errors = []
    if "collection" not in config:
        errors.append("collection セクションが見つかりません")
    elif "sources" not in config["collection"]:
        errors.append("collection.sources が見つかりません")

    if "claude" not in config:
        errors.append("claude セクションが見つかりません")

    if "delivery" not in config:
        errors.append("delivery セクションが見つかりません")

    return errors


def validate_env() -> list[str]:
    """環境変数のバリデーション。エラーメッセージのリストを返す。"""
    errors = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        errors.append("ANTHROPIC_API_KEY が設定されていません")
    return errors


class AppConfig:
    """シングルトン設定クラス。"""

    _instance: "AppConfig | None" = None
    _config: dict
    _project_root: Path

    def __init__(self) -> None:
        raise RuntimeError("AppConfig.get_instance() を使用してください")

    @classmethod
    def get_instance(cls, config_path: str | None = None) -> "AppConfig":
        if cls._instance is None:
            instance = object.__new__(cls)
            instance._project_root = _find_project_root()
            instance._config = load_config(config_path)
            load_env()
            cls._instance = instance
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """テスト用: シングルトンをリセット。"""
        cls._instance = None

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def config(self) -> dict:
        return self._config

    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット区切りキーパスでアクセス。例: config.get('claude.model')"""
        keys = key_path.split(".")
        value: Any = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_env(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)
