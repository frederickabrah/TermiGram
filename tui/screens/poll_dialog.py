from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button

class PollDialog(ModalScreen):
    """A modal screen to display poll options and allow voting."""

    def __init__(self, poll_question: str, options: list[str]):
        super().__init__()
        self.poll_question = poll_question
        self.options = options

    def compose(self) -> ComposeResult:
        with Vertical(id="poll_container"):
            yield Static(f"[bold]Poll:[/bold] {self.poll_question}")
            yield Static("Select an option to vote:")
            for i, option_text in enumerate(self.options):
                yield Button(f"{i+1}. {option_text}", id=f"poll_option_{i}")
            yield Button("Cancel", variant="default", id="cancel_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with the selected option index or None if cancelled."""
        event.stop()
        if event.button.id.startswith("poll_option_"):
            option_index = int(event.button.id.split("_")[-1])
            self.dismiss(option_index)
        elif event.button.id == "cancel_button":
            self.dismiss(None)
