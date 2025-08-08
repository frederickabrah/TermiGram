import os
from textual.widgets import Header, Footer, RichLog, Input, Static
from textual.worker import Worker
from telethon.errors import SessionPasswordNeededError, FloodWaitError

from telegram_client.client import TelegramManager
from tui.screens.login import LoginScreen
from tui.widgets.chat_list import ChatList
from tui.widgets.message_view import MessageView

class TermiGramApp(App):
    """The main application class for TermiGram."""

    TITLE = "TermiGram"
    SUB_TITLE = "Your Telegram in the Terminal"
    CSS_PATH = "style.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Horizontal(id="main_app_container")
        yield Footer()
        yield Static("Initializing...", id="status_bar")

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.status_bar = self.query_one("#status_bar")
        self.status_bar.update("Connecting to Telegram...")
        self.run_worker(self.connect_to_telegram, exclusive=True)

    async def connect_to_telegram(self) -> None:
        """Worker to handle the Telegram connection and login flow."""
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        if not api_id or not api_hash:
            self.status_bar.update("[bold red]Error: API_ID and API_HASH must be set in .env file.[/bold red]")
            return

        self.tg_manager = TelegramManager(int(api_id), api_hash)
        
        try:
            await self.tg_manager.connect()
            self.status_bar.update("Connected to Telegram. Checking authorization...")

            if not await self.tg_manager.is_authorized():
                self.status_bar.update("User not authorized. Starting login process...")
                
                phone = await self.show_login_prompt("Enter your phone number (e.g., +1234567890):")
                await self.tg_manager.send_code(phone)
                
                code = await self.show_login_prompt("Enter the code you received:")
                
                try:
                    await self.tg_manager.sign_in(phone, code)
                except SessionPasswordNeededError:
                    password = await self.show_login_prompt("Enter your 2FA password:", is_password=True)
                    await self.tg_manager.sign_in_password(password)

            me = await self.tg_manager.get_me()
            self.sub_title = f"Logged in as {me.first_name}"
            self.status_bar.update(f"[bold green]Successfully logged in as {me.first_name}![/bold green]")
            
            # Set up message handler for real-time updates
            self.tg_manager.set_message_handler(self.handle_incoming_message)

            # Now, load the main UI
            self.run_worker(self.load_main_ui, exclusive=True)

        except FloodWaitError as e:
            self.status_bar.update(f"[bold yellow]Flood wait: Please wait {e.seconds} seconds.[/bold yellow]")
        except Exception as e:
            self.status_bar.update(f"[bold red]An error occurred during connection: {e}[/bold red]")

    async def load_main_ui(self) -> None:
        """Worker to load the main chat interface after login."""
        self.status_bar.update("Loading chats...")
        main_container = self.query_one("#main_app_container")
        
        # Create the layout
        self.chat_list_widget = ChatList()
        self.message_view_widget = MessageView()
        self.message_input = Input(placeholder="Type your message here...", id="message_input")
        
        await main_container.mount(
            self.chat_list_widget,
            Vertical(
                self.message_view_widget,
                self.message_input,
                id="right_panel"
            )
        )
        
        # Fetch and display chats
        self.chat_list_table = self.chat_list_widget.query_one("#chat_list_table")
        try:
            self.chats = await self.tg_manager.get_chats()
            # Store chat entities by ID for easy lookup
            self.chat_entities = {chat.id: chat for chat in self.chats}

            for chat in self.chats:
                # Use chat.id as row_key for easy lookup later
                self.chat_list_table.add_row(chat.title or chat.name, chat.message.message if chat.message else "", key=chat.id)
            self.status_bar.update("Chats loaded. Select a chat to begin.")
        except Exception as e:
            self.status_bar.update(f"[bold red]Error loading chats: {e}[/bold red]")

        # Set up event listeners
        self.chat_list_table.on_row_selected = self.on_chat_selected
        self.message_input.on_submit = self.on_message_input_submit

    async def on_chat_selected(self, event) -> None:
        """Handle chat selection from the list."""
        # Use event.row_key directly as it's the chat ID
        selected_chat = self.chat_entities.get(event.row_key)
        
        if selected_chat:
            self.current_chat = selected_chat
            self.sub_title = f"Chatting with {selected_chat.title or selected_chat.name}"
            self.status_bar.update(f"Selected chat: {selected_chat.title or selected_chat.name}")
            await self.load_messages_for_chat(selected_chat)

    async def load_messages_for_chat(self, chat) -> None:
        """Load and display messages for the given chat."""
        self.message_view_widget.query_one("#message_log").clear()
        self.message_view_widget.query_one("#message_log").write(f"[bold blue]Loading messages for {chat.title or chat.name}...[/bold blue]")
        self.status_bar.update(f"Loading messages for {chat.title or chat.name}...")
        
        try:
            messages = await self.tg_manager.get_messages(chat, limit=50) # Fetch last 50 messages
            
            self.message_view_widget.query_one("#message_log").clear() # Clear again before displaying
            for msg in reversed(messages): # Display in chronological order
                sender = "Me"
                if msg.sender:
                    sender = msg.sender.first_name or msg.sender.username or "Unknown"
                
                display_message = msg.message
                if msg.photo:
                    display_message = "[Photo]"
                elif msg.sticker:
                    display_message = "[Sticker]"
                elif msg.document:
                    display_message = f"[File: {msg.document.attributes[0].file_name}]" if msg.document.attributes else "[File]"
                elif msg.voice:
                    display_message = "[Voice Message]"
                elif msg.video:
                    display_message = "[Video]"
                elif msg.geo:
                    display_message = "[Location]"
                elif msg.contact:
                    display_message = "[Contact]"
                elif msg.game:
                    display_message = "[Game]"
                elif msg.invoice:
                    display_message = "[Invoice]"
                elif msg.poll:
                    display_message = "[Poll]"
                elif msg.web_preview:
                    display_message = f"[Link: {msg.web_preview.url}]"
                elif msg.empty:
                    display_message = "[Empty Message]"
                elif not msg.message: # Fallback for messages with no text but other content
                    display_message = "[Unsupported Message Type]"
                
                self.message_view_widget.query_one("#message_log").write(f"[bold green]{sender}:[/bold green] {display_message}")
            
            self.message_view_widget.query_one("#message_log").scroll_end(animate=False) # Scroll to bottom
            self.status_bar.update(f"Messages loaded for {chat.title or chat.name}.")
        except Exception as e:
            self.status_bar.update(f"[bold red]Error loading messages: {e}[/bold red]")

    async def on_message_input_submit(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        if self.current_chat and event.value:
            message_text = event.value
            self.message_input.value = "" # Clear input
            self.status_bar.update("Sending message...")
            
            try:
                await self.tg_manager.send_message(self.current_chat, message_text)
                
                # Optimistically add message to view
                self.message_view_widget.query_one("#message_log").write(f"[bold green]Me:[/bold green] {message_text}")
                self.message_view_widget.query_one("#message_log").scroll_end(animate=False)
                self.status_bar.update("Message sent.")
            except Exception as e:
                self.status_bar.update(f"[bold red]Error sending message: {e}[/bold red]")
        else:
            self.status_bar.update("[bold red]Error: No chat selected or message is empty.[/bold red]")

    async def handle_incoming_message(self, message) -> None:
        """Handle an incoming message and update the UI."""
        # Update the chat list first
        await self.update_chat_list_for_new_message(message)

        # Only update message view if the message belongs to the currently selected chat
        if self.current_chat and message.chat_id == self.current_chat.id:
            sender = "Me"
            if message.sender:
                sender = message.sender.first_name or message.sender.username or "Unknown"
            
            display_message = message.message
            if message.photo:
                display_message = "[Photo]"
            elif message.sticker:
                display_message = "[Sticker]"
            elif message.document:
                display_message = f"[File: {message.document.attributes[0].file_name}]" if message.document.attributes else "[File]"
            elif message.voice:
                display_message = "[Voice Message]"
            elif message.video:
                display_message = "[Video]"
            elif message.geo:
                display_message = "[Location]"
            elif message.contact:
                display_message = "[Contact]"
            elif message.game:
                display_message = "[Game]"
            elif message.invoice:
                display_message = "[Invoice]"
            elif message.poll:
                display_message = "[Poll]"
            elif message.web_preview:
                display_message = f"[Link: {message.web_preview.url}]"
            elif message.empty:
                display_message = "[Empty Message]"
            elif not message.message: # Fallback for messages with no text but other content
                display_message = "[Unsupported Message Type]"

            self.message_view_widget.query_one("#message_log").write(f"[bold yellow]{sender}:[/bold yellow] {display_message}")
            self.message_view_widget.query_one("#message_log").scroll_end(animate=False)

    async def update_chat_list_for_new_message(self, message) -> None:
        """Update the chat list when a new message arrives."""
        # Find the chat in our current list
        chat_id = message.chat_id
        updated_chat = None
        for chat in self.chats:
            if chat.id == chat_id:
                updated_chat = chat
                break
        
        if updated_chat:
            # Remove the old entry if it exists
            if chat_id in self.chat_list_table.row_keys:
                self.chat_list_table.remove_row(chat_id)
            
            # Add it back to the top with the new message content
            self.chat_list_table.add_row(updated_chat.title or updated_chat.name, message.message, key=chat_id, index=0)
            self.chat_list_table.cursor_row = 0 # Keep cursor on the first row

    async def show_login_prompt(self, prompt: str, is_password: bool = False) -> str:
        """Utility to show a login modal and return the result."""
        login_screen = LoginScreen(prompt, is_password)
        result = await self.push_screen_wait(login_screen)
        return result

    async def on_message_input_submit(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        if self.current_chat and event.value:
            message_text = event.value
            self.message_input.value = "" # Clear input
            self.status_bar.update("Sending message...")
            
            try:
                await self.tg_manager.send_message(self.current_chat, message_text)
                
                # Optimistically add message to view
                self.message_view_widget.query_one("#message_log").write(f"[bold green]Me:[/bold green] {message_text}")
                self.message_view_widget.query_one("#message_log").scroll_end()
                self.status_bar.update("Message sent.")
            except Exception as e:
                self.status_bar.update(f"[bold red]Error sending message: {e}[/bold red]")
        else:
            self.status_bar.update("[bold red]Error: No chat selected or message is empty.[/bold red]")

    async def handle_incoming_message(self, message) -> None:
        """Handle an incoming message and update the UI."""
        # Update the chat list first
        await self.update_chat_list_for_new_message(message)

        # Only update message view if the message belongs to the currently selected chat
        if self.current_chat and message.chat_id == self.current_chat.id:
            sender = msg.sender.first_name or msg.sender.username or "Unknown"
            
                display_message = msg.message
                if msg.photo:
                    display_message = "[Photo]"
                elif msg.sticker:
                    display_message = "[Sticker]"
                elif msg.document:
                    display_message = f"[File: {msg.document.attributes[0].file_name}]" if msg.document.attributes else "[File]"
                elif msg.voice:
                    display_message = "[Voice Message]"
                elif msg.video:
                    display_message = "[Video]"
                elif msg.geo:
                    display_message = "[Location]"
                elif msg.contact:
                    display_message = "[Contact]"
                elif msg.game:
                    display_message = "[Game]"
                elif msg.invoice:
                    display_message = "[Invoice]"
                elif msg.poll:
                    display_message = "[Poll]"
                elif msg.web_preview:
                    display_message = f"[Link: {msg.web_preview.url}]"
                elif msg.empty:
                    display_message = "[Empty Message]"
                elif not msg.message: # Fallback for messages with no text but other content
                    display_message = "[Unsupported Message Type]"
                
                self.message_view_widget.query_one("#message_log").write(f"[bold green]{sender}:[/bold green] {display_message}")
            
            self.message_view_widget.query_one("#message_log").scroll_end(animate=False) # Scroll to bottom
        
        if self.current_chat and message.chat_id == self.current_chat.id:
            sender = "Me"
            if message.sender:
                sender = message.sender.first_name or message.sender.username or "Unknown"
            
            display_message = message.message
            if message.photo:
                display_message = "[Photo]"
            elif message.sticker:
                display_message = "[Sticker]"
            elif message.document:
                display_message = f"[File: {message.document.attributes[0].file_name}]" if message.document.attributes else "[File]"
            elif message.voice:
                display_message = "[Voice Message]"
            elif message.video:
                display_message = "[Video]"
            elif message.geo:
                display_message = "[Location]"
            elif message.contact:
                display_message = "[Contact]"
            elif message.game:
                display_message = "[Game]"
            elif message.invoice:
                display_message = "[Invoice]"
            elif message.poll:
                display_message = "[Poll]"
            elif message.web_preview:
                display_message = f"[Link: {message.web_preview.url}]"
            elif message.empty:
                display_message = "[Empty Message]"
            elif not message.message: # Fallback for messages with no text but other content
                display_message = "[Unsupported Message Type]"

            self.message_view_widget.query_one("#message_log").write(f"[bold yellow]{sender}:[/bold yellow] {display_message}")
            self.message_view_widget.query_one("#message_log").scroll_end()

    async def update_chat_list_for_new_message(self, message) -> None:
        """Update the chat list when a new message arrives."""
        # Find the chat in our current list
        chat_id = message.chat_id
        updated_chat = None
        for chat in self.chats:
            if chat.id == chat_id:
                updated_chat = chat
                break
        
        if updated_chat:
            # Remove the old entry if it exists
            if chat_id in self.chat_list_table.row_keys:
                self.chat_list_table.remove_row(chat_id)
            
            # Add it back to the top with the new message content
            self.chat_list_table.add_row(updated_chat.title or updated_chat.name, message.message, key=chat_id, index=0)
            self.chat_list_table.cursor_row = 0 # Keep cursor on the first row

    async def show_login_prompt(self, prompt: str, is_password: bool = False) -> str:
        """Utility to show a login modal and return the result."""
        login_screen = LoginScreen(prompt, is_password)
        result = await self.push_screen_wait(login_screen)
        return result
