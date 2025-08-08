# TermiGram Project TODO

## Phase 1: Core Chat Functionality (In Progress)

- [x] Create project directory structure.
- [ ] Create `todo.md` to track progress.
- [ ] Initialize `git` repository.
- [ ] Create `requirements.txt` with initial dependencies (`textual`, `telethon`, `python-dotenv`).
- [ ] Create the main application entry point (`main.py`).
- [ ] Implement the basic Textual app structure in `tui/app.py`.
- [ ] Implement the Telegram client wrapper in `telegram_client/client.py`.
- [ ] Build the secure authentication flow:
    - [ ] Create a login screen (`tui/screens/login.py`).
    - [ ] Handle phone number, code, and 2FA password prompts.
    - [ ] Securely save and load the Telethon session.
- [ ] Build the main chat interface:
    - [ ] Create the chat list widget (`tui/widgets/chat_list.py`).
    - [ ] Create the message view widget (`tui/widgets/message_view.py`).
    - [ ] Assemble the main layout in `tui/app.py`.
- [ ] Implement real-time message receiving and UI updates.
- [ ] Implement sending plain text messages.

## Phase 2: Enhanced Features (Not Started)

- [ ] Display message timestamps more clearly.
- [ ] Add support for message replies (viewing and sending).
- [ ] Add support for editing and deleting messages.
- [ ] View basic media (e.g., show a placeholder for images/files).
- [ ] Add a user/chat profile view.

## Phase 3: Advanced Functionality (Not Started)

- [ ] Implement global search for messages and users.
- [ ] Allow creating new groups and channels.
- [ ] Render simple stickers or emoji.
