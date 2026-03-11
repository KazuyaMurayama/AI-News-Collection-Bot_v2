"""指数バックオフリトライデコレータ"""

import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_wait: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """指数バックオフリトライデコレータ。

    config.yamlのretryセクションから設定を取得することも可能。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "%s: %d回リトライ後に失敗: %s", func.__name__, max_attempts, e
                        )
                        raise
                    wait = min(
                        backoff_base * (backoff_multiplier ** (attempt - 1)),
                        max_wait,
                    )
                    logger.warning(
                        "%s: 試行 %d/%d 失敗 (%s), %.1f秒後にリトライ",
                        func.__name__,
                        attempt,
                        max_attempts,
                        e,
                        wait,
                    )
                    time.sleep(wait)
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
