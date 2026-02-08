# TermiGram Project TODO

## Phase 1: Core Chat Functionality (Completed)

- [x] Create project directory structure.
- [x] Create `todo.md` to track progress.
- [x] Initialize `git` repository.
- [x] Create `requirements.txt` with initial dependencies (`textual`, `telethon`, `python-dotenv`).
- [x] Create the main application entry point (`main.py`).
- [x] Implement the basic Textual app structure in `tui/app.py`.
- [x] Implement the Telegram client wrapper in `telegram_client/client.py`.
- [x] Build the secure authentication flow:
    - [x] Create a login screen (`tui/screens/login.py`).
    - [x] Handle phone number, code, and 2FA password prompts.
    - [x] Securely save and load the Telethon session.
- [x] Build the main chat interface:
    - [x] Create the chat list widget (`tui/widgets/chat_list.py`).
    - [x] Create the message view widget (`tui/widgets/message_view.py`).
    - [x] Assemble the main layout in `tui/app.py`.
- [x] Implement real-time message receiving and UI updates.
- [x] Implement sending plain text messages.
- [x] Implement basic error handling and UI feedback via status bar.
- [x] Handle various message types (photo, sticker, document, etc.) with placeholders.
- [x] Ensure message view scrolls to bottom correctly.
- [x] Improve chat list updates for incoming messages (reordering).

## Phase 2: Enhanced Features (Completed)

- [x] Display message timestamps more clearly.
- [x] Add support for message replies (viewing).
- [x] Add support for message replies (sending).
- [x] Add support for editing and deleting messages (key bindings and placeholder actions).
- [x] View basic media (download functionality added, UI integration pending).
- [x] Add a user/chat profile view (key binding and placeholder action).

## Phase 3: Advanced Functionality (Completed)

- [x] Implement global search for messages and users (key binding and placeholder action).
- [x] Allow creating new groups and channels (key binding and placeholder action).
- [x] Render simple stickers or emoji.

## Phase 4: Completing Advanced Features (Completed)

- [x] **Implement full reply functionality:**
    - [x] Allow users to select a specific message to reply to.
    - [x] Update `action_reply_to_message` to use the selected message ID.
    - [x] Visually indicate the message being replied to in the input area.
- [x] **Implement media saving with UI:**
    - [x] Create a UI for selecting media from a message.
    - [x] Integrate `tg_manager.download_media` with the UI.
    - [x] Provide feedback on download progress and completion.
- [x] **Implement message editing:**
    - [x] Allow users to select their own message for editing.
    - [x] Populate the input field with the message content for editing.
    - [x] Send the edited message via `tg_manager`.
    - [x] Update the UI to reflect the edited message.
- [x] **Implement message deletion:**
    - [x] Allow users to select their own message for deletion.
    - [x] Confirm deletion with the user.
    - [x] Send the delete command via `tg_manager`.
    - [x] Remove the message from the UI.
- [x] **Implement global search:**
    - [x] Create a search input and display search results.
    - [x] Integrate with Telegram API for global message/user search.
    - [x] Allow navigation to search results.
- [x] **Implement new chat/group creation:**
    - [x] Create a UI for initiating new chats or groups.
    - [x] Allow selecting contacts or adding members for groups.
    - [x] Integrate with Telegram API for creating new entities.
- [x] **Render media and stickers:**
    - [x] Explore options for rendering images (photos, stickers) directly in the terminal (e.g., using `chafa` or similar libraries if compatible with Textual).
    - [x] If direct rendering is not feasible, improve placeholder descriptions for media.
- [x] **Improve message display:**
    - [x] Display sender names more clearly for incoming messages.
    - [x] Handle different message entities (bold, italics, links) for rich text display.
- [x] **Error Handling and User Feedback:**
    - [x] Enhance error messages for better user understanding.
    - [x] Implement more robust loading indicators.

## Phase 5: Finalizing TUI Enhancements

- [x] **Fix `AttributeError`:** Initialize `self.message_input = None` in the `__init__` method of `TermiGramApp` in `tui/app.py`.
- [x] **Implement Message Reactions:**
    - [x] Add a new binding `R` for "React to Message" in `tui/app.py`.
    - [x] Add the `action_react_to_message` method to `tui/app.py`.
    - [x] Create a `ReactionDialog` screen in `tui/screens/reaction_dialog.py`.
    - [x] Add a `send_reaction` method to `telegram_client/client.py`.
- [x] **Display Message Reactions:**
    - [x] Modify `_format_message_text` in `tui/app.py` to display reactions for each message.