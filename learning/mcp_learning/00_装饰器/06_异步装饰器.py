"""
06 - 异步装饰器

MCP 的工具处理函数几乎都是 async def（协议是异步的）。
用同步装饰器去包异步函数，是最容易踩的坑之一。

核心规则：
  * 被装饰函数是 async def 时，wrapper 也必须是 async def，并在里面 await。
  * 同步 wrapper 只能"原样返回 coroutine 对象"，一旦想在调用后做点什么就废了。
  * 一个健壮的装饰器应该同时兼容同步函数和异步函数（用 inspect.iscoroutinefunction 判断）。

运行：
    python "06_异步装饰器.py"
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
from typing import Any, Awaitable, Callable

# ---------------------------------------------------------------------------
# 1. 正确的异步装饰器
# ---------------------------------------------------------------------------


def async_timer(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)      # 必须 await
        finally:
            cost = (time.perf_counter() - start) * 1000
            print(f"    [async_timer] {func.__name__} 耗时 {cost:.1f} ms")

    return wrapper


@async_timer
async def fetch_data(key: str) -> str:
    await asyncio.sleep(0.05)
    return f"data:{key}"


# ---------------------------------------------------------------------------
# 2. 反例：用同步装饰器包异步函数
# ---------------------------------------------------------------------------


def sync_wrong(func: Callable[..., Any]) -> Callable[..., Any]:
    """错误示范 1：不 await，还想在调用后做事。"""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)      # 拿到的是 coroutine，不是结果
        print("    [sync_wrong] 我拿到的其实是:", type(result).__name__)
        return result

    return wrapper


def sync_ok(func: Callable[..., Any]) -> Callable[..., Any]:
    """能"凑合"工作的同步装饰器：原样把 coroutine 交回给调用方 await。

    但它失去了在函数执行前后插入逻辑的能力（除了同步的 before）。
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print("    [sync_ok] before（同步部分可以工作）")
        return func(*args, **kwargs)        # 不 await，直接返回 coroutine

    return wrapper


@sync_wrong
async def wrong_task() -> str:
    return "wrong-ok"


@sync_ok
async def okay_task() -> str:
    return "okay-ok"


def demo_02_sync_wrapper() -> None:
    print("  await wrong_task():", asyncio.run(wrong_task()))
    print("  注意 ['sync_wrong] 我拿到的其实是: coroutine'] —— 后置逻辑写不了。")
    print("  await okay_task() :", asyncio.run(okay_task()))


# ---------------------------------------------------------------------------
# 3. 同时兼容同步/异步的通用装饰器
# ---------------------------------------------------------------------------


def universal_log(func: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"    [log/async] {func.__name__} 开始")
            result = await func(*args, **kwargs)
            print(f"    [log/async] {func.__name__} 结束 -> {result!r}")
            return result

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"    [log/sync ] {func.__name__} 开始")
        result = func(*args, **kwargs)
        print(f"    [log/sync ] {func.__name__} 结束 -> {result!r}")
        return result

    return sync_wrapper


@universal_log
def sync_job(x: int) -> int:
    return x * 2


@universal_log
async def async_job(x: int) -> int:
    await asyncio.sleep(0)
    return x * 3


def demo_03_universal() -> None:
    print("  sync_job(5) =", sync_job(5))
    print("  asyncio.run(async_job(5)) =", asyncio.run(async_job(5)))


# ---------------------------------------------------------------------------
# 4. 实战：异步重试 + 超时（MCP 调用外部 API 时非常常用）
# ---------------------------------------------------------------------------


def async_retry(
    times: int = 3,
    delay: float = 0.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last: BaseException | None = None
            for attempt in range(1, times + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    print(f"    [async_retry] 第 {attempt}/{times} 次失败: {exc!r}")
                    if attempt < times and delay:
                        await asyncio.sleep(delay)
            raise last  # type: ignore[misc]

        return wrapper

    return decorator


def async_timeout(seconds: float) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError as exc:
                raise TimeoutError(f"{func.__name__} 超过 {seconds}s 未返回") from exc

        return wrapper

    return decorator


_state = {"n": 0}


@async_timeout(1.0)
@async_retry(times=3, delay=0.01, exceptions=(ValueError,))
async def unstable_api(item_id: int) -> str:
    _state["n"] += 1
    if _state["n"] < 3:
        raise ValueError(f"模拟 5xx #{_state['n']}")
    await asyncio.sleep(0.01)
    return f"item-{item_id} 获取成功"


@async_timeout(0.05)
async def too_slow() -> str:
    await asyncio.sleep(1)
    return "永远到不了"


async def demo_04_real_world() -> None:
    print("  1) 重试 + 超时装饰器叠加（从下往上：先 retry 后 timeout）")
    print("  结果:", await unstable_api(42))
    print("  2) 超时保护:")
    try:
        await too_slow()
    except TimeoutError as exc:
        print("  预期超时:", exc)
    print("  3) 并发 3 个调用:")
    results = await asyncio.gather(*(async_job(i) for i in range(1, 4)))
    print("  结果:", results)


if __name__ == "__main__":
    print("=" * 70)
    print("1. 正确的异步装饰器")
    print("=" * 70)
    print("  asyncio.run(fetch_data('k1')) =", asyncio.run(fetch_data("k1")))
    print()

    print("=" * 70)
    print("2. 同步装饰器包异步函数")
    print("=" * 70)
    demo_02_sync_wrapper()
    print()

    print("=" * 70)
    print("3. 通用装饰器（同步/异步通吃）")
    print("=" * 70)
    demo_03_universal()
    print()

    print("=" * 70)
    print("4. 实战：异步重试 + 超时")
    print("=" * 70)
    asyncio.run(demo_04_real_world())
