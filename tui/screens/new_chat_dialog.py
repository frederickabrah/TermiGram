from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Button, Input, Label, RadioSet, RadioButton

class NewChatDialog(ModalScreen):
    """A modal screen for creating new chats or groups."""

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="new_chat_dialog_container"):
            yield Label("Create New:", classes="dialog_label")
            with RadioSet(id="chat_type_radios"):
                yield RadioButton("Group", id="radio_group")
                yield RadioButton("Channel", id="radio_channel")

            yield Label("Title:", classes="dialog_label")
            yield Input(placeholder="Enter title", id="chat_title_input")

            yield Label("Participants (usernames, comma-separated, for groups only):")
            yield Input(placeholder="user1, user2", id="chat_participants_input")

            yield Label("About (for channels only):")
            yield Input(placeholder="Optional description", id="channel_about_input")

            with Horizontal(classes="dialog_buttons"):
                yield Button("Create", variant="primary", id="create_chat_button")
                yield Button("Cancel", variant="default", id="cancel_button")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle changes in chat type selection."""
        if event.pressed.id == "radio_group":
            self.query_one("#chat_participants_input").display = True
            self.query_one("#channel_about_input").display = False
        elif event.pressed.id == "radio_channel":
            self.query_one("#chat_participants_input").display = False
            self.query_one("#channel_about_input").display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create_chat_button":
            chat_type = self.query_one(RadioSet).pressed_button.id.replace("radio_", "")
            title = self.query_one("#chat_title_input").value
            participants = [u.strip() for u in self.query_one("#chat_participants_input").value.split(',')] if chat_type == "group" else []
            about = self.query_one("#channel_about_input").value if chat_type == "channel" else None
            self.dismiss({"type": chat_type, "title": title, "participants": participants, "about": about})
        elif event.button.id == "cancel_button":
            self.dismiss(None)
