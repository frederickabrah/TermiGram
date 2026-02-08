from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label

class ConfirmDialog(ModalScreen):
    """A modal screen for confirming an action."""

    def __init__(self, prompt_text: str):
        super().__init__()
        self.prompt_text = prompt_text

    def compose(self) -> ComposeResult:
        with Grid(id="confirm_dialog_grid"):
            yield Label(self.prompt_text, id="confirm_prompt")
            yield Button("Yes", variant="primary", id="confirm_yes_button")
            yield Button("No", variant="default", id="confirm_no_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with the appropriate result."""
        event.stop()
        if event.button.id == "confirm_yes_button":
            self.dismiss(True)
        else:
            self.dismiss(False)
