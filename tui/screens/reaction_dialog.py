from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Button

class ReactionDialog(ModalScreen):
    """A modal screen to display reaction options and allow selection."""

    DEFAULT_REACTIONS = ["👍", "❤️", "😂", "🔥", "🎉", "🤩", "🙏", "💯", "😢", "🤮", "💩", "👎"]

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="reaction_container"):
            yield Static("Select a reaction:")
            with Horizontal(id="reaction_buttons"):
                for reaction in self.DEFAULT_REACTIONS:
                    yield Button(reaction, id=f"reaction_{reaction}")
            yield Button("Cancel", variant="default", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with the selected reaction or None if cancelled."""
        event.stop()
        if event.button.id.startswith("reaction_"):
            reaction = event.button.id.split("_")[-1]
            self.dismiss(reaction)
        elif event.button.id == "cancel_button":
            self.dismiss(None)
