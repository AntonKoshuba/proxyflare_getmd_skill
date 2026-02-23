import asyncio

import httpx

from proxyflare.client.manager import ProxyflareWorkersManager
from proxyflare.client.transport import AsyncProxyflareTransport


async def check_ip(client, request_id):
    try:
        # Добавляем случайный параметр, чтобы избежать кеширования на стороне Cloudflare
        url = f"https://httpbin.org/ip?test={request_id}"
        resp = await client.get(url)
        ip = resp.json().get("origin")
        print(f"🚀 Запрос #{request_id}: Выходной IP -> {ip}")
    except Exception as e:
        print(f"❌ Запрос #{request_id} ошибка: {e}")


async def main():
    # Инициализируем менеджер, указывая путь к JSON с воркерами
    try:
        manager = ProxyflareWorkersManager(source="proxyflare-workers.json")
    except Exception as e:
        print(f"🔴 Ошибка загрузки воркеров: {e}")
        return

    # Создаем асинхронный транспорт
    transport = AsyncProxyflareTransport(manager)

    print(f"📡 В пуле: {len(manager.workers)} нод(ы).")
    print("Запускаем параллельную проверку...\n")

    # Передаем наш транспорт в клиент httpx
    async with httpx.AsyncClient(transport=transport, timeout=15.0) as client:
        # Запускаем 5 запросов одновременно
        tasks = [check_ip(client, i) for i in range(1, 6)]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
