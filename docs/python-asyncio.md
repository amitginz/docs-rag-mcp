# Python asyncio

## Event loop
asyncio runs coroutines on a single-threaded event loop. A coroutine is defined with `async def` and only runs when it is awaited or scheduled as a task. While one coroutine waits for I/O, the loop switches to another, so thousands of network calls can share one thread.

## Tasks and gather
`asyncio.create_task()` schedules a coroutine to run concurrently. `asyncio.gather()` waits for several awaitables and returns their results in order. Use `return_exceptions=True` so one failure does not cancel the others.

## Blocking code
CPU-heavy or blocking calls freeze the whole loop. Move them to a thread with `asyncio.to_thread()` or to a process pool. Never call `time.sleep()` inside a coroutine; use `await asyncio.sleep()` instead.

## Timeouts
Wrap slow operations with `asyncio.timeout()` (Python 3.11+) or `asyncio.wait_for()` so a stuck request cannot hang the service forever.
