
import asyncio
import sys
try:
    from app.core.database import engine
    async def test_db():
        print('Connecting...')
        async with engine.connect() as conn:
            print('Async DB query test connection successful!')
    asyncio.run(test_db())
except Exception as e:
    import traceback
    traceback.print_exc()

