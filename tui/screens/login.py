from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Input, Label, Static

class LoginScreen(ModalScreen):
    """A modal screen for prompting the user for login credentials."""

    def __init__(self, prompt_text: str, is_password: bool = False):
        super().__init__()
        self.prompt_text = prompt_text
        self.is_password = is_password

    def compose(self) -> ComposeResult:
        with Grid(id="login_grid"):
            yield Static(self.prompt_text, id="login_prompt")
            yield Input(password=self.is_password, id="login_input")
            yield Button("Submit", variant="primary", id="login_submit_button")

    def on_mount(self) -> None:
        """Focus the input when the screen is mounted."""
        self.query_one(Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismiss the screen with the input value when the button is pressed."""
        event.stop()
        self.dismiss(self.query_one(Input).value)
