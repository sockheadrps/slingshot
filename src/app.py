from textual.app import App, ComposeResult
from textual.binding import Binding
from textual import on
from textual.widgets import Header, Footer, Tabs, TabPane, Static, TabbedContent, OptionList, Button
from textual.events import Click
from textual.reactive import Reactive
from utils.env_loader import DATA_FILE, OUTPUT_FILE
from utils.file_ops import load_saved_commands, load_directories
import os

class MyApp(App):
    """A Textual app with three tabs/pages."""

    # Ensure this is a valid CSS string
    CSS = """
    TabPane {
        align: center middle;
    }
    Tabs {
        dock: top;
    }
    OptionList {
        width: 40;
    }
    Button {
        width: 40;
    }
    """

    BINDINGS = [
        Binding("escape", "home_tab", "Home Tab"),
        Binding("down", "focus_content", "Focus Content"),
        Binding("enter", "select_option", "Select Option")
    ]

    selected_directory: Reactive[str] = Reactive("")  # Keep track of selected directory

    def compose(self) -> ComposeResult:
        with TabbedContent() as self.tabbed_content:
            self.tabs = self.tabbed_content
            with TabPane(title="Home", id="home", name="Home"):
                yield self.home_tab()
            with TabPane(title="Build", id="build", name="Build"):
                yield self.build_tab()
            with TabPane(title="Customize", id="customize", name="Customize"):
                yield Static("Customize your settings here!")

    def home_tab(self) -> ComposeResult:
        # Load saved commands
        saved_commands = load_saved_commands()

        # Ensure that saved_commands is a list of strings
        if not all(isinstance(command, str) for command in saved_commands):
            raise ValueError("All commands must be strings.")

        # Wrap each command in a Static widget to display in OptionList
        command_list = [str(command) for command in saved_commands]

        return OptionList(*command_list)

    def build_tab(self) -> ComposeResult:
        """Loads all directories from DATA_FILE and returns them as OptionList."""
        # Load directories
        directories = load_directories()

        # Ensure that directories is a list of strings
        if not all(isinstance(directory, str) for directory in directories):
            raise ValueError("All directories must be strings.")

        # Wrap each directory in a Static widget to display in OptionList
        directory_list = [str(directory) for directory in directories]

        # Return the OptionList widget with directories
        return OptionList(*directory_list)

    @on(OptionList.OptionSelected)  # Register the handler for option selection events
    def on_select_option(self, event: OptionList.OptionSelected) -> None:
        """Handle selection of an option from the build list."""
        # Get the selected item (the directory)
        selected = event.option.prompt  # This is the selected directory name
        print(f"Selected directory: {selected}")
        self.selected_directory = selected

        # Display two options when an item is selected
        self.show_cd_and_write_options()

    def show_cd_and_write_options(self):
        """Display options for `cd` and `write commands`."""
        for child in self.query_one("#build").children:
            child.remove()  # Remove each child widget individually

        # Create an OptionList with cd and write commands options
        options = ["Change Directory (cd)", "Write Commands"]
        option_list = OptionList(*options, id="action_options")
        
        # Add the OptionList to the build tab
        build_tab_pane = self.query_one("#build")
        build_tab_pane.mount(option_list)
        
        # Focus the new OptionList
        option_list.focus()

        # Handle selection
        @on(OptionList.OptionSelected)
        def handle_action_selected(event: OptionList.OptionSelected) -> None:
            selected = event.option.prompt
            print(f"Selected action: {selected}")
            if selected == "Change Directory (cd)":
                self.action_cd()
            elif selected == "Write Commands":
                self.action_write_commands()

    def action_cd(self) -> None:
        """Handle cd (change directory) action."""
        print(f"Changing directory to {self.selected_directory}")
        # You can add functionality here for `cd` to the selected directory

    def action_write_commands(self) -> None:
        """Handle write commands action."""
        print(f"Writing commands for {self.selected_directory}")
        # You can add functionality here for writing commands related to the selected directory

    def action_home_tab(self):
        """Focus the home tab when escape is pressed"""
        print("Focusing home tab")
        # Set active tab to "home" tab
        self.query_one(TabbedContent).active = "home"
        # Focus the tabs widget
        self.query_one(Tabs).focus()

    def action_focus_tab_bar(self):
        """Focus the tab bar when escape is pressed"""
        print("Focusing tab bar")
        self.tabs.focus()

    def action_focus_content(self):
        """Focus the content when down is pressed"""
        print("Focusing content")
        current_tab = self.tabs.active
        if current_tab:
            tabbed_content = self.tabbed_content
            content = tabbed_content.get_pane(current_tab)

            if content:
                # Now, focus on the OptionList widget within the active TabPane
                option_list_widget = content.query(OptionList).first()
                if option_list_widget:
                    option_list_widget.focus()
                    print(f"Focused {option_list_widget}")


if __name__ == "__main__":
    app = MyApp()
    app.run()
