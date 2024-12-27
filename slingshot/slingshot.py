import os
import json
import sys
import threading
import pyperclip
import time
from pathlib import Path
from rich.table import Table
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.panel import Panel
from rich.layout import Layout
from rich.color import Color
from rich.align import Align
from pynput import keyboard
import rich
import win32gui
import win32process
import psutil
import queue
import msvcrt
import os
import dotenv



console = Console()

# Index for the currently selected directory
selected_index = 0

# Debounce delay for key press handling
DEBOUNCE_DELAY = 0.1
last_press_time = 0

selected = []
index = 0
page = 0
option_key = False
directory_index = 0
selected_panel = None
option_index = 0
show_help = False


dotenv.load_dotenv()

base_path = Path(os.getenv("BASE_DIR"))
# Path to storage.json
STORAGE_PATH = base_path / "slingshot_storage.json"

# Initialize storage if not present
if not STORAGE_PATH.exists():
    with open(STORAGE_PATH, "w") as f:
        json.dump({"directories": [], "commands": []}, f)

script_output_path = base_path / "output.txt"

# initialize the file if not present
if not Path(script_output_path).exists():
    with open(script_output_path, "w") as f:
        f.write("")


def write_output_to_file(output):
    with open(script_output_path, "w") as f:
        f.write(output)






def load_directories():
    """Load saved directories from storage."""
    with open(STORAGE_PATH, "r") as f:
        return json.load(f)["directories"]


def save_directories(directories):
    """Save directories to storage."""
    # Read existing data
    if Path(STORAGE_PATH).exists():
        with open(STORAGE_PATH, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}  # Handle empty or invalid JSON
    else:
        data = {}

    # Update directories
    data["directories"] = directories

    # Write updated data back to the file
    with open(STORAGE_PATH, "w") as f:
        json.dump(data, f, indent=4)


def load_terminal_commands():
    with open(STORAGE_PATH, "r") as f:
        data = json.load(f)
        return data["commands"]


def save_terminal_commands(command):
    with open(STORAGE_PATH, "r") as f:
        data = json.load(f)

    with open(STORAGE_PATH, "w") as f:
        if isinstance(command, list):
            data["commands"] = command
        else:
            data["commands"].append(command)
        json.dump(data, f)


def add_current_directory():
    """Add the current directory to the list of saved directories."""
    current_dir = os.getcwd()
    directories = load_directories()
    if current_dir not in directories:
        directories.append(
            {
                "directory": current_dir,
                "post_commands": []
            }
        )
        save_directories(directories)
        console.print(f"[green]Added:[/green] {current_dir}")
    else:
        console.print(
            f"[yellow]Directory already saved:[/yellow] {current_dir}")


def get_directories():
    """Display a list of saved directories in a TUI."""
    directories = load_directories()
    if not directories:
        console.print("[red]No saved directories found.[/red]")
        return None

    # Create a table
    table = Table(title="Saved Directories",
                  show_header=True, header_style="bold cyan")
    table.add_column("Index", justify="center")
    table.add_column("Directory", overflow="fold")

    # Highlight the selected directory
    for i, directory in enumerate(directories):
        if i == selected_index:
            table.add_row(
                str(i + 1), f"[bold yellow]{directory['directory']}[/bold yellow]")
        else:
            table.add_row(str(i + 1), directory['directory'])

    console.clear()
    console.print(table)


def add_custom_command(directory, command):
    directories = load_directories()
    for dir in directories:
        if dir['directory'] == directory:
            dir['post_commands'].append(command)
            save_directories(directories)
            return
    else:
        print(f"directory not found: {directory}")


def get_active_application():
    try:
        # Get the handle of the active window
        hwnd = win32gui.GetForegroundWindow()

        # Get the PID of the process owning the active window
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Use psutil to get the process name from the PID
        process = psutil.Process(pid)
        return process.name()  # Return the name of the application
    except Exception as e:
        print(f"Error while getting active application: {e}")
        return None


def create_key_handler(key_queue):
    """Create a key handler with access to the key queue."""
    def on_press(key):
        """Handle key press events and update selection."""
        global selected_index, last_press_time, show_help

        try:
            if not hasattr(on_press, 'last_press'):
                on_press.last_press = 0
            current_time = time.time()

            # Implement debounce
            if current_time - on_press.last_press < DEBOUNCE_DELAY:
                return True

            active_application = get_active_application()

            # Only process keys if the active application is "WindowsTerminal"
            if active_application == "WindowsTerminal.exe":
                if key == keyboard.Key.left:
                    key_queue.put('left')
                elif key == keyboard.Key.right:
                    key_queue.put('right')
                elif key == keyboard.Key.up:
                    key_queue.put('up')
                elif key == keyboard.Key.down:
                    key_queue.put('down')
                elif key == keyboard.Key.enter:
                    key_queue.put('enter')
                elif key == keyboard.Key.space:
                    key_queue.put('space')
                elif key == keyboard.Key.delete:
                    key_queue.put('delete')
                elif key == keyboard.KeyCode.from_char('a'):
                    key_queue.put('a')
                elif key == keyboard.KeyCode.from_char('h'):
                    key_queue.put('h')

                on_press.last_press = current_time

        except Exception as e:
            print(f"Error: {e}")
        return True  # Continue listening

    return on_press


def listen_for_arrow_keys(key_queue):
    """Start listening for arrow key presses."""
    def start_listener():
        with keyboard.Listener(on_press=create_key_handler(key_queue)) as listener:
            listener.join()

    # Start the listener in a separate thread
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()
    return listener_thread


def generate_directory_list(index, selection_made):
    global selected_panel, page, selected_panel, selected_index
    directories = load_directories()  # Load the list of directories
    selected_style = rich.style.Style(color="cyan")
    unselected_style = rich.style.Style(dim=True)
    directory_table = Table(
        show_header=False,
        expand=True,
        show_edge=False,

    )

    # Add rows to the navigation panel
    selected_dir = None
    for i, directory in enumerate(directories):
        if i == index and selected_panel == 0:
            if selection_made:
                selected_dir = directory['directory']
            directory_table.add_row(
                rich.text.Text(
                    f"> {directory['directory']}", style=selected_style)
            )
        else:
            directory_table.add_row(
                rich.text.Text(
                    f"  {directory['directory']}", style=unselected_style)
            )

    directory_panel = Panel(
        directory_table,
        title="Directories",
        box=rich.box.ROUNDED,
        border_style="cyan",
        expand=True,
        padding=1
    )

    if page == 0:
        if selected_panel == 0 and len(selected) == 0:
            directory_panel.border_style = "cyan"
        elif selected_panel == 0 and len(selected) > 0:
            directory_panel.border_style = "cyan"
        elif index == 0 and selected_panel == None and len(selected) != 0:
            directory_panel.border_style = "magenta"
        else:
            directory_panel.border_style = "dim"

    return directory_panel, selected_dir


def generate_final_command_panel(selection_made):
    global index, directory_index
    print(f"directory_index: {directory_index}")

    directories = load_directories()  # Load the list of directories
    selected_style = rich.style.Style(color="cyan")
    unselected_style = rich.style.Style(dim=True)
    final_command_table = Table(
        show_header=False,
        style=selected_style,
        show_edge=True,
        expand=True
    )

    # Add rows to the navigation panel
    selected_command = None
    commands = directories[directory_index]['post_commands']
    for i, command in enumerate(commands):
        if i == index:  # Highlight the current index
            if selection_made:
                selected_command = command
            final_command_table.add_row(
                rich.text.Text(
                    f"> {command}", style=selected_style)
            )
        else:
            final_command_table.add_row(
                rich.text.Text(
                    f"  {command}", style=unselected_style)
            )

    options_text = Text("Press a to add custom command", style="dim")
    layout = Layout()
    layout.split_column(
        Layout(final_command_table, name="final_command_table", ratio=9),
        Layout(options_text, name="options_text", ratio=1),
    )

    final_command_panel = Panel(
        layout,
        box=rich.box.SIMPLE_HEAD,
        border_style="dim",
        expand=True,
        padding=1
    )

    return final_command_panel, selected_command


def generate_post_command_panel(index, selection_made):
    commands = load_terminal_commands()
    selected_style = rich.style.Style(color="cyan")
    unselected_style = rich.style.Style(dim=True)

    directory_panel = Table(
        title="Post Command",
        show_header=False,
        box=rich.box.ROUNDED,
        border_style="blue",
        style="bold",
        expand=True
    )

    # Add rows to the navigation panel
    selected_command = None

    # Calculate number of columns needed
    num_commands = len(commands)
    items_per_column = 8
    num_columns = (num_commands + items_per_column - 1) // items_per_column

    # Create list to hold cells for each row
    for row in range(items_per_column):
        cells = []
        for col in range(num_columns):
            idx = row + (col * items_per_column)
            if idx < num_commands:
                command = commands[idx]
                if idx == index:  # Highlight the current index
                    if selection_made:
                        selected_command = command
                    cells.append(rich.text.Text(
                        f"> {command}", style=selected_style))
                else:
                    cells.append(rich.text.Text(
                        f"  {command}", style=unselected_style))
            else:
                cells.append(rich.text.Text(""))

        directory_panel.add_row(*cells)

    return directory_panel, selected_command


def generate_command_panel():
    """
    Generates the command panel.

    Args:
        selected (list): List of selected items.
        selected_panel (int): The index of the selected panel.
        index (int): The active index.

    Returns:
        rich.Panel: The generated command panel.
    """
    global selected, index, page, option_key, selected_panel, index, option_index

    if len(selected) > 0:
        command_table = Table(
            show_header=False, box=rich.box.SIMPLE_HEAD, style="dim", show_edge=True)
        cells = []
        for i, item in enumerate(selected):
            style = 'cyan' if option_index == i else ''
            cells.append(Text(item, style=style))
        command_table.add_row(*cells)

        command_panel = Panel(
            command_table,
            title="Command Panel",
            border_style="cyan",
            box=rich.box.ROUNDED,
        )
        if page == 0:
            if index == 1 and selected_panel is None:
                command_panel.border_style = "magenta"
            elif selected_panel == 1:
                command_panel.border_style = "cyan"
            else:
                command_panel.border_style = "dim"
    else:
        if page == 0 and not selected_panel:
            command_panel = Panel(
                "Waiting for selection...",
                title="Command Panel",
                box=rich.box.SIMPLE_HEAD,
            )
        else:
            command_panel = Panel(
                "Waiting for selection...",
                title="Command Panel",
                border_style="green",
                box=rich.box.SIMPLE_HEAD,
            )
    return command_panel


def generate_rich_interface(selection_made):
    global selected, index, page, option_key, selected_panel, show_help, directory_index

    sub_panel = None
    command_panel = None
    # print(f"selected_panel: {selected_panel} selection_made: {selection_made}")

    # Handle page panels
    if page == 0:
        # Populate the first panel with directories but don't allow interaction until selected
        command_panel = generate_command_panel()
        if selection_made:
            if selected_panel is None:
                selected_panel = index
                index = 0
                selection_made = False
        elif len(selected) == 0:
            selected_panel = 0
            sub_panel, _ = generate_directory_list(index, selection_made)
        elif len(selected) > 0:
            sub_panel, _ = generate_directory_list(index, selection_made)

        if selected_panel == 0:
            sub_panel, selected_dir = generate_directory_list(
                index, selection_made)
            if selection_made:
                selected.append(selected_dir)
                directory_index = index
                index = 0  # Reset index for the next panel
                page = 1  # Move to the next page
                selected_panel = None
        elif selected_panel == 1:
            command_panel = generate_command_panel()

    elif page == 1 and len(selected) > 0:
        sub_panel, selected_command = generate_post_command_panel(
            index, selection_made)
        if selection_made:
            selected.append(selected_command)
            # selected_panel = index
            index = 0

    elif page == 2 and len(selected) > 0:
        sub_panel, selected_command = generate_final_command_panel(
            selection_made)
        if option_key == "a":
            return
        if selection_made and not option_key == "a":
            selected.append(selected_command)
            # selected_panel = index
            index = 0

    # Generate the command panel using the helper function on any page
    if command_panel is None:
        command_panel = generate_command_panel()

    current_page_style = rich.style.Style(color="cyan", italic=True)
    other_page_style = rich.style.Style(dim=True, italic=True)
    pages = {
        0: "Directories",
        1: "General Commands",
        2: "Custom Commands"
    }

    # Create a table to hold the pages text with different colors based on current page
    pages_table = Table(show_header=False, show_edge=False, expand=True)

    page_texts = []
    for page_num, page_text in pages.items():
        if page_num == page:
            page_texts.append(Text(page_text, style=current_page_style))
        else:
            page_texts.append(Text(page_text, style=other_page_style))

    pages_table.add_row(Align.center(Text(" | ").join(page_texts)))

    page_panel = Panel(
        pages_table,
        box=rich.box.SIMPLE_HEAD,
    )

    # Help Panel
    help_command_style = rich.style.Style(underline=True, dim=True)
    left_right = Align.center("← →", style=help_command_style)
    up_down = Align.center("↑ ↓", style=help_command_style)
    enter = Align.center("Enter", style=help_command_style)
    space = Align.center("Space", style=help_command_style)
    a = Align.center("a", style=help_command_style)

    left_right_action = Align.center("Navigate pages")
    up_down_action = Align.center("Navigate options")
    enter_action = Align.center("Run command")
    space_action = Align.center("Select option")
    a_action = Align.center("Add custom command")

   # Help text aligned at the bottom
    help_text = Align.center(Text("press h to show help", style="dim italic"))

    # Help table aligned at the bottom
    help_table = Table(
        show_header=False,
        show_edge=True,
        expand=True,
        box=rich.box.ROUNDED,
        style="dim"
    )
    help_table.add_row(left_right, up_down, enter, space, a)
    help_table.add_row(left_right_action, up_down_action,
                    enter_action, space_action, a_action)

    # Wrap the help_table in Align.bottom for vertical alignment
    help_panel = Panel(
        Align.center(help_table),
        title="Help",
        box=rich.box.SIMPLE_HEAD
    )

    # Header style and text
    header_style = rich.style.Style(color="magenta", italic=True)
    main_panel_header_text = Text(f"Navigation {page + 1}", style=header_style)

    # Ensure sub_panel is always set
    if sub_panel is None:
        sub_panel = Panel("Loading...", border_style="dim cyan")


    # Combine panels into the layout
    layout = Layout()
    layout.split_column(
        Layout(page_panel, name="page_panel", ratio=1),
        Layout(sub_panel, name="sub_panel", ratio=4),
        Layout(command_panel, name="command_panel", ratio=1),
        Layout(Align.center(help_text, vertical="bottom"), name="help_text", ratio=1),
        Layout(Align.center(help_panel, vertical="bottom"), name="help_panel", ratio=2),
    )

    if show_help:
        layout["command_panel"].ratio = 1
        layout["help_panel"].visible = True
        layout["help_text"].visible = False
    else:
        layout["command_panel"].ratio = 2
        layout["help_panel"].visible = False
        layout["help_text"].visible = True

    # Main panel containing all sub-panels
    main_panel = Panel(
        layout,
        expand=False,
        height=30,
    )
    return main_panel

def interface():
    global selected, index, page, option_key, directory_index, selected_panel, option_index, show_help
    commands = load_terminal_commands()
    try:
        console = Console()
        console.clear()
        key_queue = queue.Queue()
        listener_thread = listen_for_arrow_keys(key_queue)
        pages = 2
        selection_made = False
        directories = load_directories()
        choices = 0

        with Live(generate_rich_interface(selection_made), refresh_per_second=10) as live:

            while True:
                if not key_queue.empty():
                    key = key_queue.get_nowait()
                    if page == 0:
                        if selected_panel is None:
                            choices = 2
                        elif selected_panel == 0:
                            choices = len(directories)
                        elif selected_panel == 1:
                            choices = len(selected) + 1
                    elif page == 1:
                        choices = len(commands)
                    elif page == 2:
                        choices = len(
                            directories[directory_index]['post_commands'])

                    if key == 'up':
                        if selected_panel == 1:
                            selected_panel = None
                            option_index = 0
                            index = 0
                        else:
                            if index > 0:
                                index -= 1

                    elif key == 'down':
                        if selected_panel == 1:
                            pass
                        elif selected_panel == 0 or selected_panel is None:
                            if index < choices - 1:
                                index += 1

                    elif key == 'enter':  # Quit when "Enter" is pressed
                        if not option_key == "a":
                            flush_input()
                            break
                        else:
                            option_key = None
                    elif key == 'right' and page < pages:
                        if not selected_panel:
                            if len(selected) > 0:
                                page += 1
                        else:
                            option_index += 1 if option_index < choices - 2 else 0
                            print(f"option_index: {option_index}")
                    elif key == 'left' and page >= 0:
                        if not selected_panel:
                            if len(selected) > 0:
                                page -= 1
                        else:
                            option_index -= 1 if option_index > 0 else 0
                            print(f"option_index: {option_index}")
                    elif key == 'delete':
                        option_key = "delete"
                        if selected_panel == 1:
                            selected.pop(option_index)
                            option_index -= 1
                    elif key == 'h':
                        show_help = not show_help

                    elif key == 'a':
                        if page == 2:
                            option_key = "a"
                            live.stop()  # Temporarily stop Live rendering
                            console.clear()

                            # Center the prompt using a Rich Panel
                            prompt_message = Panel(
                                "[bold yellow]Enter your custom command:[/bold yellow]",
                                title="Custom Command",
                                border_style="magenta",
                                expand=False,
                            )
                            console.print(Align.center(prompt_message))

                            # Get the user input
                            flush_input()
                            user_input_text = Prompt.ask(
                                "[bold yellow]Enter your command[/bold yellow]")

                            # Process the user input
                            if user_input_text:
                                # Add to the selection
                                selected.append(user_input_text)
                                # Save the custom command

                                add_custom_command(
                                    selected[0], user_input_text)

                                # Notify the user with a confirmation panel
                                confirmation_message = Panel(
                                    f"[bold green]Command added:[/bold green] [cyan]{
                                        user_input_text}[/cyan]",
                                    title="Success",
                                    border_style="green",
                                    expand=False,
                                )
                                console.print(Align.center(
                                    confirmation_message))
                                time.sleep(1)
                                live.start()  # Restart the Live rendering after input
                        if page == 1:
                            option_key = "a"
                            commands = load_terminal_commands()
                            live.stop()
                            console.clear()
                            flush_input()

                            prompt_message = Panel(
                                "[bold yellow]Enter your custom command:[/bold yellow]",
                                title="Custom Command",
                                border_style="magenta",
                                expand=False,
                            )
                            console.print(Align.center(prompt_message))
                            user_input_text = Prompt.ask(
                                "Enter your command")
                            if user_input_text:
                                confirmation_message = Panel(
                                    f"[bold green]Command added:[/bold green] [cyan]{
                                        user_input_text}[/cyan]",
                                    title="Success",
                                    border_style="green",
                                    expand=False,
                                )
                                console.print(Align.center(
                                    confirmation_message))
                                time.sleep(1)
                                commands = load_terminal_commands()
                                commands.append(user_input_text.lstrip())
                                save_terminal_commands(commands)
                                live.start()

                        live.update(generate_rich_interface(
                            selection_made))  # Update the interface

                    elif key == 'space':
                        selection_made = True
                        live.update(generate_rich_interface(selection_made))
                        index = 0

                    if selection_made:
                        selection_made = False
                    live.update(generate_rich_interface(selection_made))
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
    finally:
        listener_thread.join(timeout=1.0)  # Ensure listener stops
        console.clear()
        return selected


def handle_command(args):
    """Handle command-line arguments."""
    if len(args) == 1:
        selected = interface()
        write_output_to_file("\n".join([str(item)
                             for item in selected]) + "\n")
        quit(0)
    elif len(args) == 2:
        if args[1] == "add":
            add_current_directory()
        else:
            print("Invalid command")
            quit(1)


if __name__ == "__main__":
    handle_command(sys.argv)
