import httpx

class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def _post(self, method: str, payload: dict):
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/{method}", json=payload)
            r.raise_for_status()
            return r.json()

    async def send_message(self, chat_id: str, text: str):
        return await self._post("sendMessage", {
            "chat_id": chat_id,
            "text": text
        })
