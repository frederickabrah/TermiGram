import os
from dotenv import load_dotenv
from tui.app import TermiGramApp

def main():
    """Main function to run the app."""
    load_dotenv()
    app = TermiGramApp()
    app.run()

if __name__ == "__main__":
    main()
