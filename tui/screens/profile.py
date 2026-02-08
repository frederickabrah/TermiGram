from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button

class ProfileScreen(ModalScreen):
    """A modal screen to display user or chat profile information."""

    def __init__(self, entity_info: dict):
        super().__init__()
        self.entity_info = entity_info

    def compose(self) -> ComposeResult:
        with Vertical(id="profile_container"):
            yield Static(f"[bold]ID:[/bold] {self.entity_info.get('id')}")
            yield Static(f"[bold]Name:[/bold] {self.entity_info.get('name')}")
            yield Static(f"[bold]Username:[/bold] @{self.entity_info.get('username')}")
            if self.entity_info.get('bio'):
                yield Static(f"[bold]Bio:[/bold] {self.entity_info.get('bio')}")
            yield Button("Close", variant="primary", id="close_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen when the button is pressed."""
        event.stop()
        self.dismiss()
