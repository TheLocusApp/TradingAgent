# Latest Fix Attempt - Hybrid Pattern

## Approach

Since the working examples show **subscribe first, then listen**, but we're getting KeyError when subscribing first, the issue might be that channels need to be initialized by calling `listen()` first.

## New Pattern: Listen → Subscribe → Iterate

```python
# 1. Call listen() to create/initialize channels
quote_stream = self.streamer.listen(Quote)

# 2. Wait for internal channel setup
await asyncio.sleep(0.3)

# 3. Subscribe (channels should now exist)
await self._subscribe_pending()

# 4. Consume the stream
async for quote in quote_stream:
    # process quotes
```

## Why This Should Work

- Calling `listen()` might initialize internal state needed for channels
- The 0.3s wait gives time for async initialization
- Subscribe happens after channels are initialized
- Then we consume the already-created stream

## If This Still Fails

The next approach would be to actually start iterating (get first quote) before subscribing, which would definitely create channels.


