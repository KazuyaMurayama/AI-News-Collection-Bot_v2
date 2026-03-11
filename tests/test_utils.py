"""ユーティリティモジュールのテスト"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.utils.config import AppConfig, load_config, validate_config, validate_env
from src.utils.logger import setup_logger
from src.utils.retry import with_retry


class TestConfig:
    def setup_method(self):
        AppConfig.reset()

    def test_load_config(self, tmp_path):
        config_data = {
            "app": {"name": "test"},
            "collection": {"sources": []},
            "claude": {"model": "test"},
            "delivery": {},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))
        assert config["app"]["name"] == "test"

    def test_validate_config_valid(self):
        config = {
            "collection": {"sources": []},
            "claude": {"model": "test"},
            "delivery": {},
        }
        errors = validate_config(config)
        assert errors == []

    def test_validate_config_missing(self):
        errors = validate_config({})
        assert len(errors) == 3

    def test_validate_env_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            errors = validate_env()
            assert any("ANTHROPIC_API_KEY" in e for e in errors)

    def test_validate_env_present(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            errors = validate_env()
            assert errors == []

    def test_app_config_get(self, tmp_path):
        config_data = {
            "claude": {"model": "test-model", "temperature": 0.5},
            "collection": {"sources": []},
            "delivery": {},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        instance = AppConfig.get_instance(str(config_file))
        assert instance.get("claude.model") == "test-model"
        assert instance.get("claude.temperature") == 0.5
        assert instance.get("nonexistent.key", "default") == "default"
        AppConfig.reset()


class TestLogger:
    def test_setup_logger(self, tmp_path):
        logger = setup_logger("test_logger", log_dir=str(tmp_path))
        assert logger.name == "test_logger"
        assert len(logger.handlers) == 2  # console + file

    def test_no_duplicate_handlers(self, tmp_path):
        logger = setup_logger("test_dup", log_dir=str(tmp_path))
        logger2 = setup_logger("test_dup", log_dir=str(tmp_path))
        assert len(logger2.handlers) == 2


class TestRetry:
    def test_success_first_try(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_then_succeed(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        result = fail_then_succeed()
        assert result == "ok"
        assert call_count == 3

    def test_all_retries_fail(self):
        @with_retry(max_attempts=2, backoff_base=0.01)
        def always_fail():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            always_fail()

    def test_retry_on_specific_exception(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff_base=0.01, retry_on=(ValueError,))
        def fail_with_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("not retried")

        with pytest.raises(TypeError):
            fail_with_type_error()
        assert call_count == 1
