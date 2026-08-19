#!/usr/bin/env python3
import subprocess
import sys
from textual.app import App
from textual.containers import Container
from textual.widgets import Static, Button, Input

logo = r'''
[bold cyan]
 ██████╗ ██████╗ ██╗██████╗ ███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝ ██╔══██╗██║██╔══██╗██╔════╝██║     ██╔═══██╗██║    ██║
██║  ███╗██████╔╝██║██║  ██║█████╗  ██║     ██║   ██║██║ █╗ ██║
██║   ██║██╔══██╗██║██║  ██║██╔══╝  ██║     ██║   ██║██║███╗██║
╚██████╔╝██║  ██║██║██████╔╝██║     ███████╗╚██████╔╝╚███╔███╔╝
 ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
[/bold cyan]
'''

class gridflow(App):
    CSS = """
    .hidden { display: none; }
    .error { color: red; }
    """
    def compose(self):
        self.static = Static(logo)
        yield self.static
        

        #Buttons for SSH Sessions
        yield Button("[bold white]Manage SSH Sessions[/bold white]", id="manage_ssh")
        yield Button("[bold white]Create SSH Session[/bold white]", id="create_ssh")
        yield Static("[bold yellow]SSH Keys Only! No Passwords![/bold yellow]") 
        #Spawn SSH session
        self.create_form = Container(
                Static("Create SSH Session", classes="form_title"),
                Input(placeholder="Username: ", id="username"),
                Input(placeholder="IP: ", type="text", id="ssh_ip"),
                Input(placeholder="Full Key Path: ", id="key_path"),
                Input(placeholder="Port Number: ", id="listener_port"),
                Button("Submit", id="submit_ssh", variant="primary"),
                classes="hidden",
        )
        yield self.create_form
        
        self.error_alert = Static("", classes="error")
        yield self.error_alert

    def customize_tui(self):
        self.static.styles.text_align = "center" 
    
    def on_button_pressed(self, event):
        if event.button.id == "create_ssh":
            self.create_form.remove_class("hidden")
            self.error_alert.update("")

        elif event.button.id == "submit_ssh":
            username = self.query_one("#username", Input).value.strip()
            ssh_ip = self.query_one("#ssh_ip", Input).value.strip()
            key_path = self.query_one("#key_path", Input).value.strip()
            listener_port = self.query_one("#listener_port", Input).value.strip()
            cmd = [
                "ssh",
                "-i", key_path,
                "-fND", listener_port,
                f"{username}@{ssh_ip}"
            ]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                self.error_alert.update(f"Error: {e}")
                
            self.create_form.add_class("hidden")

if __name__ == "__main__":
    app = gridflow()
    app.run()
