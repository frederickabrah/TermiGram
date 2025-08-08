import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import User

class TelegramManager:
    """Manages all interactions with the Telegram API via Telethon."""

    def __init__(self, api_id: int, api_hash: str, session_name: str = "termi_gram_session"):
        """Initialize the Telegram Manager."""
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.phone = None
        self.message_handler_callback = None

    async def connect(self):
        """Connect to the Telegram servers."""
        await self.client.connect()

    async def is_authorized(self) -> bool:
        """Check if the user is already authorized."""
        return await self.client.is_user_authorized()

    async def send_code(self, phone: str):
        """Send a verification code to the user's phone."""
        self.phone = phone
        await self.client.send_code_request(phone)

    async def sign_in(self, phone: str, code: str):
        """Sign in the user with the provided code."""
        await self.client.sign_in(phone, code)

    async def sign_in_password(self, password: str):
        """Sign in with a 2FA password."""
        await self.client.sign_in(password=password)

    async def get_me(self) -> User:
        """Get the currently logged-in user."""
        return await self.client.get_me()

    async def get_chats(self):
        """Get a list of the user's chats (dialogs)."""
        return await self.client.get_dialogs()

    async def get_messages(self, chat_entity, limit: int = 50):
        """Get messages for a given chat entity."""
        messages = []
        async for message in self.client.iter_messages(chat_entity, limit=limit):
            messages.append(message)
        return messages

    async def send_message(self, chat_entity, message_text: str):
        """Send a message to a given chat entity."""
        await self.client.send_message(chat_entity, message_text)

    def set_message_handler(self, callback):
        """Set a callback function to handle incoming messages."""
        self.message_handler_callback = callback
        @self.client.on(events.NewMessage)
        async def handler(event):
            if self.message_handler_callback:
                await self.message_handler_callback(event.message)
