import os
from textual.widgets import Header, Footer, Input, Static, DataTable
from textual.worker import Worker
from telethon import errors as telethon_errors
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import (
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityStrike,
    MessageEntityUnderline,
    MessageEntityUrl,
    MessageEntityTextUrl,
)
import webbrowser
import timg
from PIL import Image
from datetime import datetime
from textual.reactive import reactive
from textual.binding import Binding
from textual.events import Key
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical

from telegram_client.client import TelegramManager
from tui.screens.login import LoginScreen
from tui.screens.new_chat_dialog import NewChatDialog
from tui.screens.profile import ProfileScreen
from tui.screens.poll_dialog import PollDialog
from tui.screens.reaction_dialog import ReactionDialog
from tui.widgets.chat_list import ChatList
from tui.widgets.message_view import MessageView



class TermiGramApp(App):
    """The main application class for TermiGram."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_input = Input(placeholder="Type your message here...", id="message_input")
        self.chat_list_widget = ChatList()
        self.message_view_widget = MessageView()

    TITLE = "TermiGram"
    SUB_TITLE = "Your Telegram in the Terminal"
    CSS_PATH = "style_dark.css"

    BINDINGS = [
        Binding("r", "reply_to_message", "Reply to message", show=True),
        Binding("e", "edit_message", "Edit message", show=True),
        Binding("d", "delete_message", "Delete message", show=True),
        Binding("s", "save_media", "Save media", show=True),
        Binding("o", "open_link", "Open link", show=True),
        Binding("p", "view_profile", "View profile", show=True),
        Binding("/", "global_search", "Search", show=True),
        Binding("n", "new_chat", "New Chat", show=True),
        Binding("T", "toggle_theme", "Toggle Theme", show=True),
        Binding("V", "vote_in_poll", "Vote in Poll", show=True),
        Binding("R", "react_to_message", "React to Message", show=True),
    ]

    THEMES = {
        "dark": "style_dark.css",
        "light": "style_light.css",
    }
    current_theme_index = 0

    reply_to_message_id = reactive(None)
    selected_message_content = reactive(None) # To store content of selected message for reply preview

    def action_toggle_theme(self) -> None:
        """Action to toggle between available themes."""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.THEMES)
        theme_name = list(self.THEMES.keys())[self.current_theme_index]
        self.css_path = self.THEMES[theme_name]
        self.recompose()
        self.status_bar.update(f"Switched to {theme_name} theme.")

    async def on_message_selected(self, event: DataTable.RowSelected) -> None:
        """
        Handles the selection of a message in the message view.
        Sets the message ID for a potential reply.
        """
        self.reply_to_message_id = event.row_key
        # Get the full message object to display in the input preview
        selected_message = self.messages.get(event.row_key)
        if selected_message:
            formatted_message_content = await self._format_message_text(selected_message)
            self.selected_message_content = f"Replying to {selected_message.sender.first_name or selected_message.sender.username or 'Unknown'}: {formatted_message_content}"
        else:
            self.selected_message_content = ""
        self.status_bar.update(f"Selected message ID for reply: {self.reply_to_message_id}. Press 'r' to reply.")
        self.message_input.focus()

    def action_reply_to_message(self) -> None:
        """Prepares the app to reply to the selected message."""
        if self.reply_to_message_id:
            self.status_bar.update(f"Replying to message ID: {self.reply_to_message_id}. Type your reply.")
            self.message_input.focus()
        else:
            self.status_bar.update("No message selected to reply to. Select a message first.")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Horizontal(
            self.chat_list_widget,
            Vertical(
                self.message_view_widget,
                self.message_input,
                id="right_panel"
            ),
            id="main_app_container"
        )
        yield Footer()
        yield Static("Initializing...", id="status_bar")

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        self.status_bar = self.query_one("#status_bar")
        self.status_bar.update("Connecting to Telegram...")
        self.run_worker(self.connect_to_telegram, exclusive=True)

    def watch_selected_message_content(self, content: str | None) -> None:
        """
        Watches for changes in selected_message_content and updates the input placeholder
        to show a preview of the message being replied to.
        """
        if self.message_input is not None: # Check if message_input has been composed yet
            if content:
                self.message_input.placeholder = f"Replying to: {content}"
            else:
                self.message_input.placeholder = "Type your message here..."

    async def connect_to_telegram(self) -> None:
        """
        Handles the connection to Telegram, including the login flow if necessary.
        This runs in a worker to avoid blocking the UI.
        """
        api_id = os.getenv("API_ID")
        api_hash = os.getenv("API_HASH")
        if not api_id or not api_hash:
            self.status_bar.update("[bold red]Error: API_ID and API_HASH must be set in .env file.[/bold red]")
            return

        self.tg_manager = TelegramManager(int(api_id), api_hash)
        
        try:
            # Connect to the Telegram servers
            await self.tg_manager.connect()
            self.status_bar.update("Connected to Telegram. Checking authorization...")

            # If not authorized, start the login process
            if not await self.tg_manager.is_authorized():
                self.status_bar.update("User not authorized. Starting login process...")
                
                phone = await self.show_login_prompt("Enter your phone number (e.g., +1234567890):")
                await self.tg_manager.send_code(phone)
                
                code = await self.show_login_prompt("Enter the code you received:")
                
                try:
                    await self.tg_manager.sign_in(phone, code)
                except SessionPasswordNeededError:
                    # Handle 2FA if enabled
                    password = await self.show_login_prompt("Enter your 2FA password:", is_password=True)
                    await self.tg_manager.sign_in_password(password)

            # Get user info and update the UI
            me = await self.tg_manager.get_me()
            self.sub_title = f"Logged in as {me.first_name}"
            self.status_bar.update(f"[bold green]Successfully logged in as {me.first_name}![/bold green]")
            
            # Set up a handler for incoming messages
            self.tg_manager.set_message_handler(self.handle_incoming_message)

            # Load the main chat UI
            self.run_worker(self.load_main_ui, exclusive=True)
            self.chat_list_widget.focus() # Set initial focus to the chat list

        except FloodWaitError as e:
            self.status_bar.update(f"[bold yellow]Flood wait: Please wait {e.seconds} seconds.[/bold yellow]")
        except (telethon_errors.rpcerrorlist.ApiIdInvalidError, telethon_errors.rpcerrorlist.PhoneNumberInvalidError, telethon_errors.rpcerrorlist.PhoneCodeInvalidError, telethon_errors.rpcerrorlist.PasswordHashInvalidError) as e:
            self.status_bar.update(f"[bold red]Telegram authentication error: {e}[/bold red]")
        except (ConnectionError, TimeoutError) as e:
            self.status_bar.update(f"[bold red]Network connection error: {e}[/bold red]")
        except Exception as e:
            self.status_bar.update(f"[bold red]An unexpected error occurred: {e}[/bold red]")

    async def load_main_ui(self) -> None:
        """
        Loads the main chat interface after a successful login.
        This includes the chat list and message view.
        """
        self.status_bar.update("Loading chats...")
        main_container = self.query_one("#main_app_container")
        self.chat_list_table = self.query_one("#chat_list_table")
        self.message_view_widget = self.query_one("#message_table")
        
        # Create the main layout components
        # self.chat_list_widget = ChatList()
        # self.message_view_widget = MessageView()
        # self.message_input = Input(placeholder="Type your message here...", id="message_input")
        
        
        
        # Fetch and display the user's chats
        self.chat_list_table = self.chat_list_widget.query_one("#chat_list_table")
        try:
            self.chats = await self.tg_manager.get_chats()
            # Store chat entities in a dictionary for easy lookup by ID
            self.chat_entities = {chat.id: chat for chat in self.chats}

            for chat in self.chats:
                # Use chat.id as the row_key for easy lookup later
                self.chat_list_table.add_row(chat.title or chat.name, chat.message.message if chat.message else "", key=chat.id)
            self.status_bar.update("Chats loaded. Select a chat to begin.")
        except Exception as e:
            self.status_bar.update(f"[bold red]Error loading chats: {e}[/bold red]")

        # Set up event listeners for the UI components
        self.chat_list_table.on_row_selected = self.on_data_table_row_selected
        self.message_input.on_submit = self.on_message_input_submit
        self.query_one("#message_table").on_row_selected = self.on_message_selected

    

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        print("Chat selected!")

    async def load_messages_for_chat(self, chat) -> None:
        """
        Clears the message view, fetches messages for the selected chat,
        and displays them.
        """
        # Clear the message view and display a loading message
        message_table = self.message_view_widget.query_one(DataTable)
        message_table.clear()
        message_table.add_row("", "", f"[bold blue]Loading messages for {chat.title or chat.name}...[/bold blue]")
        self.status_bar.update(f"Loading messages for {chat.title or chat.name}...")
        
        try:
            messages = await self.tg_manager.get_messages(chat, limit=50)
            
            message_table.clear() # Clear again before displaying
            
            self.messages = {} # Store messages by ID for easy lookup
            for msg in reversed(messages): # Display in chronological order
                self.messages[msg.id] = msg # Store the full message object
                sender = "Me"
                if msg.sender:
                    sender = msg.sender.first_name or msg.sender.username or "Unknown"
                timestamp = msg.date.strftime("%H:%M") # Format as HH:MM
                
                display_message = await self._format_message_text(msg)
                reply_info = ""
                if msg.reply_to_msg_id:
                    reply_info = "[Replying to a message] "
                
                message_table.add_row(timestamp, sender, f"{reply_info}{display_message}", key=msg.id)
            
            message_table.scroll_end(animate=False) # Scroll to the bottom
            self.status_bar.update(f"Messages loaded for {chat.title or chat.name}.")
        except telethon_errors.rpcerrorlist.ChatSendForbiddenError:
            self.status_bar.update("[bold red]Error: You don't have permission to view messages in this chat.[/bold red]")
        except telethon_errors.rpcerrorlist.ChannelPrivateError:
            self.status_bar.update("[bold red]Error: This is a private channel and you don't have access.[/bold red]")
        except telethon_errors.rpcerrorlist.UserBlockedError:
            self.status_bar.update("[bold red]Error: You have blocked this user or they have blocked you.[/bold red]")
        except Exception as e:
            self.status_bar.update(f"[bold red]An unexpected error occurred while loading messages: {e}[/bold red]")

    async def on_message_input_submit(self, event: Input.Submitted) -> None:
        """Handles the submission of a message from the input field."""
        if self.current_chat and event.value:
            message_text = event.value
            self.message_input.value = "" # Clear the input field
            self.status_bar.update("Sending message...")
            
            try:
                # If in editing mode, edit the message
                if self.editing_message_id:
                    await self.tg_manager.edit_message(self.current_chat, self.editing_message_id, message_text)
                    self.status_bar.update("Message edited.")
                    self.editing_message_id = None # Clear editing mode
                    # Refresh messages to show the edited content
                    await self.load_messages_for_chat(self.current_chat)
                else:
                    # Otherwise, send a new message
                    await self.tg_manager.send_message(self.current_chat, message_text, reply_to_msg_id=self.reply_to_message_id)
                    
                    # Optimistically add the message to the view with the current time
                    now = datetime.now().strftime("%H:%M")
                    message_table = self.message_view_widget.query_one(DataTable)
                    message_table.add_row(now, "Me", message_text)
                    message_table.scroll_end(animate=False)
                    self.status_bar.update("Message sent.")
                self.reply_to_message_id = None # Clear reply mode
                self.selected_message_content = None # Clear reply preview
            except Exception as e:
                self.status_bar.update(f"[bold red]Error sending message: {e}[/bold red]")
        else:
            self.status_bar.update("[bold red]Error: No chat selected or message is empty.[/bold red]")

    async def handle_incoming_message(self, message) -> None:
        """
        Handles an incoming message from the Telegram client and updates the UI.
        """
        # Update the chat list to show the new message at the top
        await self.update_chat_list_for_new_message(message)

        # Only update the message view if the message belongs to the currently selected chat
        if self.current_chat and message.chat_id == self.current_chat.id:
            if message.sender:
                sender = message.sender.first_name or message.sender.username or "Unknown"
            if message.sender.is_self:
                sender = "Me"
            timestamp = message.date.strftime("%H:%M") # Format as HH:MM
            
            display_message = await self._format_message_text(message)

            reply_info = ""
            if message.reply_to_msg_id:
                reply_info = "[Replying to a message] "

            message_table = self.message_view_widget.query_one(DataTable)
            message_table.add_row(timestamp, sender, f"{reply_info}{display_message}", key=message.id)
            message_table.scroll_end(animate=False)

    def action_edit_message(self) -> None:
        """Action to trigger message editing."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_to_edit = self.messages[self.reply_to_message_id]
            # Only allow editing of your own messages
            if message_to_edit.out:
                self.editing_message_id = self.reply_to_message_id
                self.message_input.value = message_to_edit.message
                self.message_input.focus()
                self.status_bar.update(f"Editing message ID: {self.editing_message_id}. Modify text and press Enter.")
            else:
                self.status_bar.update("You can only edit your own messages.")
        else:
            self.status_bar.update("No message selected for editing.")

    def action_delete_message(self) -> None:
        """Action to trigger message deletion."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_to_delete = self.messages[self.reply_to_message_id]
            # For now, only allow deleting your own messages
            if message_to_delete.out:
                self.run_worker(self._confirm_and_delete_message, message_to_delete)
            else:
                self.status_bar.update("You can only delete your own messages.")
        else:
            self.status_bar.update("No message selected for deletion.")

    async def _confirm_and_delete_message(self, message_to_delete) -> None:
        """Confirm deletion with the user and then delete the message."""
        confirm = await self.push_screen_wait(ConfirmDialog("Are you sure you want to delete this message?"))
        if confirm:
            self.status_bar.update(f"Deleting message ID: {message_to_delete.id}...")
            try:
                await self.tg_manager.delete_message(self.current_chat, [message_to_delete.id])
                self.status_bar.update("Message deleted.")
                # Remove the message from the UI
                message_table = self.message_view_widget.query_one(DataTable)
                message_table.remove_row(message_to_delete.id)
                del self.messages[message_to_delete.id]
                self.reply_to_message_id = None
                self.selected_message_content = None
            except Exception as e:
                self.status_bar.update(f"[bold red]Error deleting message: {e}[/bold red]")
        else:
            self.status_bar.update("Message deletion cancelled.")

    async def action_save_media(self) -> None:
        """Action to save media from a selected message."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_to_save = self.messages[self.reply_to_message_id]
            if message_to_save.media:
                self.status_bar.update(f"Downloading media from message ID: {self.reply_to_message_id}...")
                try:
                    file_path = await self.tg_manager.download_media(message_to_save)
                    if file_path:
                        self.status_bar.update(f"[bold green]Media saved to: {file_path}[/bold green]")
                    else:
                        self.status_bar.update("[bold yellow]No media found in selected message.[/bold yellow]")
                except Exception as e:
                    self.status_bar.update(f"[bold red]Error saving media: {e}[/bold red]")
            else:
                self.status_bar.update("[bold yellow]Selected message does not contain media.[/bold yellow]")
        else:
            self.status_bar.update("No message selected or selected message does not exist.")

    async def action_open_link(self) -> None:
        """Action to open a link from the selected message in the default web browser."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_with_link = self.messages[self.reply_to_message_id]
            if message_with_link.entities:
                for entity in message_with_link.entities:
                    if isinstance(entity, MessageEntityUrl) or isinstance(entity, MessageEntityTextUrl):
                        url = entity.url or message_with_link.message[entity.offset : entity.offset + entity.length]
                        try:
                            webbrowser.open(url)
                            self.status_bar.update(f"[bold green]Opened link: {url}[/bold green]")
                            return
                        except Exception as e:
                            self.status_bar.update(f"[bold red]Error opening link: {e}[/bold red]")
                self.status_bar.update("[bold yellow]No clickable link found in the selected message.[/bold yellow]")
            else:
                self.status_bar.update("[bold yellow]No entities (including links) found in the selected message.[/bold yellow]")
        else:
            self.status_bar.update("No message selected or selected message does not exist.")

    async def action_vote_in_poll(self) -> None:
        """Action to vote in a poll."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_with_poll = self.messages[self.reply_to_message_id]
            if message_with_poll.poll:
                poll_question = message_with_poll.poll.question
                poll_options = [option.text for option in message_with_poll.poll.results.options]
                
                chosen_option_index = await self.push_screen_wait(PollDialog(poll_question, poll_options))
                
                if chosen_option_index is not None:
                    try:
                        await self.tg_manager.send_poll_vote(message_with_poll, [chosen_option_index])
                        self.status_bar.update(f"[bold green]Voted for option {chosen_option_index + 1} in poll.[/bold green]")
                        # Refresh messages to show updated poll results
                        await self.load_messages_for_chat(self.current_chat)
                    except Exception as e:
                        self.status_bar.update(f"[bold red]Error voting in poll: {e}[/bold red]")
                else:
                    self.status_bar.update("Poll vote cancelled.")
            else:
                self.status_bar.update("[bold yellow]Selected message is not a poll.[/bold yellow]")
        else:
            self.status_bar.update("No message selected or selected message does not exist.")

    async def action_react_to_message(self) -> None:
        """Action to send a reaction to the selected message."""
        if self.reply_to_message_id and self.reply_to_message_id in self.messages:
            message_to_react = self.messages[self.reply_to_message_id]
            selected_reaction = await self.push_screen_wait(ReactionDialog())
            if selected_reaction:
                try:
                    await self.tg_manager.send_reaction(self.current_chat, message_to_react, selected_reaction)
                    self.status_bar.update(f"[bold green]Sent reaction {selected_reaction} to message.[/bold green]")
                    # Refresh messages to show updated reactions
                    await self.load_messages_for_chat(self.current_chat)
                except Exception as e:
                    self.status_bar.update(f"[bold red]Error sending reaction: {e}[/bold red]")
            else:
                self.status_bar.update("Reaction cancelled.")
        else:
            self.status_bar.update("No message selected or selected message does not exist.")

    async def show_login_prompt(self, prompt: str, is_password: bool = False) -> str:
        """Shows a login prompt screen and returns the input."""
        screen = LoginScreen(prompt, is_password)
        result = await self.push_screen_wait(screen)
        return result

    async def _view_profile(self, chat) -> None:
        """Worker to get and display the profile information."""
        self.status_bar.update(f"Fetching profile for {chat.title or chat.name}...")
        try:
            entity = await self.tg_manager.get_entity(chat)
            if entity:
                full_user = None
                if hasattr(entity, 'id'):
                    full_user = await self.tg_manager.get_full_user(entity.id)

                profile_info = {
                    'id': entity.id,
                    'name': f"{entity.first_name or ''} {entity.last_name or ''}".strip(),
                    'username': entity.username,
                    'bio': full_user.about if full_user else None,
                }
                await self.push_screen_wait(ProfileScreen(profile_info))
            else:
                self.status_bar.update("Could not fetch profile information.")
        except Exception as e:
            self.status_bar.update(f"[bold red]Error fetching profile: {e}[/bold red]")

    def action_global_search(self) -> None:
        """Action to trigger a global search for messages."""
        self.run_worker(self._perform_global_search)

    async def _perform_global_search(self) -> None:
        """Prompts for a search query, performs the search, and displays the results."""
        query = await self.show_login_prompt("Enter search query:")
        if query:
            self.status_bar.update(f"Searching for '{query}'...")
            try:
                results = await self.tg_manager.search_messages(query)
                if results:
                    selected_message_id = await self.push_screen_wait(SearchResultsScreen(query, results))
                    if selected_message_id:
                        # Find the chat of the selected message and load it
                        selected_message = next((msg for msg in results if msg.id == selected_message_id), None)
                        if selected_message and selected_message.chat_id:
                            # Find the chat entity in our current list of chats
                            target_chat = self.chat_entities.get(selected_message.chat_id)
                            if target_chat:
                                self.current_chat = target_chat
                                self.sub_title = f"Chatting with {target_chat.title or target_chat.name}"
                                self.status_bar.update(f"Selected chat: {target_chat.title or target_chat.name}")
                                await self.load_messages_for_chat(target_chat)
                                # TODO: Scroll to the specific message in the loaded chat
                                self.status_bar.update(f"Loaded chat and navigated to message ID: {selected_message_id}")
                            else:
                                self.status_bar.update("[bold yellow]Could not find chat for selected message.[/bold yellow]")
                        else:
                            self.status_bar.update("[bold yellow]Selected message or its chat not found.[/bold yellow]")
                else:
                    self.status_bar.update(f"No results found for '{query}'.")
            except Exception as e:
                self.status_bar.update(f"[bold red]Error during global search: {e}[/bold red]")
        else:
            self.status_bar.update("Global search cancelled.")

    def action_new_chat(self) -> None:
        """Action to create a new group or channel."""
        self.run_worker(self._perform_new_chat_creation)

    async def _perform_new_chat_creation(self) -> None:
        """Prompts for new chat/group details and creates it."""
        result = await self.push_screen_wait(NewChatDialog())
        if result:
            chat_type = result["type"]
            title = result["title"]
            self.status_bar.update(f"Creating new {chat_type}: {title}... [bold yellow]Loading...[/bold yellow]")
            try:
                if chat_type == "group":
                    participants = result["participants"]
                    # Note: A more complete implementation would fetch user entities first
                    # to resolve usernames to Telethon User objects.
                    new_entity = await self.tg_manager.create_group(title, participants)
                elif chat_type == "channel":
                    about = result["about"]
                    new_entity = await self.tg_manager.create_channel(title, about=about)
                
                self.status_bar.update(f"[bold green]{chat_type.capitalize()} '{title}' created successfully![/bold green]")
                # Refresh the chat list to show the new chat
                self.chats = await self.tg_manager.get_chats()
                self.chat_entities = {chat.id: chat for chat in self.chats}
                self.chat_list_table.clear()
                for chat in self.chats:
                    self.chat_list_table.add_row(chat.title or chat.name, chat.message.message if chat.message else "", key=chat.id)

            except Exception as e:
                self.status_bar.update(f"[bold red]Error creating {chat_type}: {e}[/bold red]")
        else:
            self.status_bar.update("New chat/group creation cancelled.")

    async def update_chat_list_for_new_message(self, message) -> None:
        """Updates the chat list when a new message arrives."""
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
            self.chat_list_table.cursor_row = 0 # Keep the cursor on the first row

    async def _format_message_text(self, message) -> str:
        """
        Formats the message text, replacing media with placeholders and applying
        text formatting (bold, italic, etc.) based on message entities.
        """
        text = message.message or ""
        # Replace media with placeholders or render images
        if message.photo:
            try:
                # Download the photo to a temporary file
                file_path = await self.tg_manager.download_media(message, path=".cache/")
                if file_path:
                    # Open the image and render it to a string
                    img = Image.open(file_path)
                    renderer = timg.Renderer()
                    text = renderer.render_rgb(img, max_width=40) # Adjust max_width as needed
                    os.remove(file_path) # Clean up the temporary file
                else:
                    text = "[Photo]"
            except Exception as e:
                text = f"[Photo - Error rendering: {e}]"
        elif message.sticker:
            text = f"{message.sticker.emoji} [Sticker]" if message.sticker.emoji else "[Sticker]"
        elif message.document:
            text = f"[File: {message.document.attributes[0].file_name}]" if message.document.attributes else "[File]"
        elif message.voice:
            text = "[Voice Message]"
        elif message.video:
            text = "[Video]"
        elif message.geo:
            text = "[Location]"
        elif message.contact:
            text = "[Contact]"
        elif message.game:
            text = "[Game]"
        elif message.invoice:
            text = "[Invoice]"
        elif message.poll:
            poll_text = f"[POLL] {message.poll.question}\n"
            for option in message.poll.results.options:
                percentage = (option.voters / message.poll.results.total_voters * 100) if message.poll.results.total_voters > 0 else 0
                poll_text += f"  - {option.text} ({option.voters} votes, {percentage:.1f}%)\n"
            text = poll_text.strip()
        elif message.web_preview:
            text = f"[Link: {message.web_preview.url}]"
        elif message.empty:
            text = "[Empty Message]"
        elif not message.message: # Fallback for messages with no text but other content
            text = "[Unsupported Message Type]"

        # Display reactions if available
        if message.reactions:
            reaction_summary = " ".join([f"{r.emoticon}({r.count})" for r in message.reactions.results])
            text = f"{text}\n[reactions] {reaction_summary} [/reactions]"

        # Apply entity formatting (bold, italic, etc.)
        if message.entities and message.message:
            formatted_text = []
            last_offset = 0
            for entity in message.entities:
                formatted_text.append(message.message[last_offset:entity.offset])
                entity_text = message.message[entity.offset : entity.offset + entity.length]
                
                if isinstance(entity, MessageEntityBold):
                    formatted_text.append(f"[bold]{entity_text}[/bold]")
                elif isinstance(entity, MessageEntityItalic):
                    formatted_text.append(f"[italic]{entity_text}[/italic]")
                elif isinstance(entity, MessageEntityCode):
                    formatted_text.append(f"[code]{entity_text}[/code]")
                elif isinstance(entity, MessageEntityPre):
                    formatted_text.append(f"[pre]{entity_text}[/pre]")
                elif isinstance(entity, MessageEntityStrike):
                    formatted_text.append(f"[strike]{entity_text}[/strike]")
                elif isinstance(entity, MessageEntityUnderline):
                    formatted_text.append(f"[underline]{entity_text}[/underline]")
                elif isinstance(entity, MessageEntityURL) or isinstance(entity, MessageEntityTextUrl):
                    formatted_text.append(f"[link={entity.url or entity_text}]{entity_text}[/link]")
                else:
                    formatted_text.append(entity_text) # Fallback for unsupported entities
                last_offset = entity.offset + entity.length
            formatted_text.append(message.message[last_offset:])
            text = "".join(formatted_text)

        return text

    