import asyncio
import os
from telethon import TelegramClient, events
from telethon.tl.types import User
from telethon.tl.functions.channels import CreateChannelRequest

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

    async def send_message(self, chat_entity, message_text: str, reply_to_msg_id: int = None):
        """Send a message to a given chat entity."""
        await self.client.send_message(chat_entity, message_text, reply_to=reply_to_msg_id)

    async def edit_message(self, chat_entity, message_id: int, new_text: str):
        """Edit an existing message."""
        await self.client.edit_message(chat_entity, message_id, new_text)

    async def delete_message(self, chat_entity, message_ids: list[int]):
        """Delete messages."""
        await self.client.delete_messages(chat_entity, message_ids)

    async def search_messages(self, query: str, limit: int = 50):
        """Search messages globally."""
        messages = []
        async for message in self.client.iter_messages(None, search=query, limit=limit):
            messages.append(message)
        return messages

    async def create_group(self, title: str, users: list):
        """Create a new group with specified users."""
        return await self.client.iter_create_group(title, users=users)

    async def create_channel(self, title: str, about: str = None):
        """Create a new channel."""
        return await self.client(CreateChannelRequest(title=title, about=about))

    async def download_media(self, message, path: str = "downloads/"):
        """Download media from a message to a specified path."""
        if message.media:
            # Ensure the directory exists
            os.makedirs(path, exist_ok=True)
            file_path = await message.download_media(file=path)
            return file_path
        return None

    def set_message_handler(self, callback):
        """Set a callback function to handle incoming messages."""
        self.message_handler_callback = callback
        @self.client.on(events.NewMessage)
        async def handler(event):
            if self.message_handler_callback:
                await self.message_handler_callback(event.message)

    async def get_entity(self, entity):
        """Get the full entity (user, chat, or channel)."""
        return await self.client.get_entity(entity)

    async def get_full_user(self, user_entity):
        """Get the full user object, including bio."""
        return await self.client.get_full_user(user_entity)

    async def send_poll_vote(self, message, options: list[int]):
        """Send a vote to a poll."""
        await message.click(options=options)

    async def send_reaction(self, message, reaction: str):
        """Send a reaction to a message."""
        await message.react(reaction)
