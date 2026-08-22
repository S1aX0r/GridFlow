#!/usr/bin/env python3

import subprocess
import uuid

from textual.app import App
from textual.containers import Container, Vertical
from textual.widgets import Static, Button, Input 

logo = r"""
[bold cyan]
 ██████╗ ██████╗ ██╗██████╗ ███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝ ██╔══██╗██║██╔══██╗██╔════╝██║     ██╔═══██╗██║    ██║
██║  ███╗██████╔╝██║██║  ██║█████╗  ██║     ██║   ██║██║ █╗ ██║
██║   ██║██╔══██╗██║██║  ██║██╔══╝  ██║     ██║   ██║██║███╗██║
╚██████╔╝██║  ██║██║██████╔╝██║     ███████╗╚██████╔╝╚███╔███╔╝
 ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝  ╚══════╝╚═════╝  ╚══╝╚══╝
Memory Stored SSH Session Manager
[/bold cyan]
"""


class GridFlow(App):
    CSS = """
    .hidden {
        display: none;
    }

    .error {
        color: red;
    }

    .session {
        border: round cyan;
    }

    .session Button {
    }
    """

    def __init__(self):
        super().__init__()

        # Session settings are kept only in memory.
        # They will disappear when the application closes KEEP APPLICATION RUNNING.
        self.sessions = []

        self.ssh_processes = {}

    def compose(self):
        self.static = Static(logo)
        yield self.static

        yield Button(
            "[bold white]Manage SSH Sessions[/bold white]",
            id="manage_ssh",
        )

        yield Button(
            "[bold white]Create SSH Session[/bold white]",
            id="create_ssh",
        )

        yield Static(
            "[bold yellow]SSH Keys Only! No Passwords![/bold yellow]"
        )

        yield Static(
            "[bold yellow]All SSH sessions are stored in memory! Stopping GridFlow will kill all SSH sessions![/bold yellow]"
        )

        self.create_form = Container(
            Static("Create SSH Session", classes="form_title"),

            Input(
                placeholder="Username",
                id="username",
            ),

            Input(
                placeholder="IP address or hostname",
                id="ssh_ip",
            ),

            Input(
                placeholder="Full key path",
                id="key_path",
            ),

            Input(
                placeholder="SOCKS port number",
                id="listener_port",
            ),

            Button(
                "Submit",
                id="submit_ssh",
                variant="primary",
            ),

            Button(
                "Cancel",
                id="cancel_create",
            ),

            classes="hidden",
        )

        yield self.create_form

        self.sessions_panel = Vertical(classes="hidden")
        yield self.sessions_panel

        self.error_alert = Static("", classes="error")
        yield self.error_alert

    def on_mount(self):
        self.refresh_sessions_panel()

    def refresh_sessions_panel(self):

        for child in list(self.sessions_panel.children):
            child.remove()

        if not self.sessions:
            self.sessions_panel.mount(
                Static("No SSH sessions have been created.")
            )
            return

        self.sessions_panel.mount(
            Static("[bold cyan]SSH Session Manager[/bold cyan]")
        )

        for session in self.sessions:
            session_id = session["id"]
            process = self.ssh_processes.get(session_id)

            if process and process.poll() is None:
                status = "[bold green]Active[/bold green]"
            else:
                status = "[bold yellow]Inactive[/bold yellow]"

            session_text = (
                f"[bold cyan]"
                f"{session['username']}@{session['ssh_ip']}"
                f"[/bold cyan]\n"
                f"Key: {session['key_path']}\n"
                f"SOCKS port: {session['listener_port']}\n"
                f"Status: {status}"
            )

            self.sessions_panel.mount(
                Container(
                    Static(session_text),

                    Button(
                        "Reconnect",
                        id=f"reconnect_{session_id}",
                        variant="primary",
                    ),

                    Button(
                        "Kill SSH Session",
                        id=f"kill_{session_id}",
                        variant="error",
                    ),

                    Button(
                        "Delete",
                        id=f"delete_{session_id}",
                    ),

                    classes="session",
                )
            )

    def start_ssh_session(self, session):

        session_id = session["id"]

        existing_process = self.ssh_processes.get(session_id)

        if (
            existing_process
            and existing_process.poll() is None
        ):
            self.error_alert.update(
                "This SSH session is already running."
            )
            return

        cmd = [
            "ssh",
            "-i",
            session["key_path"],
            "-ND",
            session["listener_port"],
            f"{session['username']}@{session['ssh_ip']}",
        ]

        try:
            process = subprocess.Popen(cmd)

            self.ssh_processes[session_id] = process

            self.error_alert.update(
                f"SSH session started: "
                f"{session['username']}@{session['ssh_ip']}"
            )

            self.refresh_sessions_panel()

        except Exception as error:
            self.error_alert.update(
                f"Error starting SSH session: {error}"
            )

    def kill_ssh_session(self, session_id):
        """Terminate one selected SSH session."""

        process = self.ssh_processes.get(session_id)

        if not process or process.poll() is not None:
            self.error_alert.update(
                "That SSH session is not currently running."
            )

            self.ssh_processes.pop(session_id, None)
            self.refresh_sessions_panel()
            return

        try:
            process.terminate()
            process.wait(timeout=5)

            self.ssh_processes.pop(session_id, None)

            self.error_alert.update(
                "SSH session terminated."
            )

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

            self.ssh_processes.pop(session_id, None)

            self.error_alert.update(
                "SSH session was forcefully killed."
            )

        except Exception as error:
            self.error_alert.update(
                f"Error killing SSH session: {error}"
            )

        self.refresh_sessions_panel()

    def delete_ssh_session(self, session_id):

        process = self.ssh_processes.get(session_id)

        if process and process.poll() is None:
            self.error_alert.update(
                "Kill the active SSH session before deleting it."
            )
            return

        self.ssh_processes.pop(session_id, None)

        self.sessions = [
            session
            for session in self.sessions
            if session["id"] != session_id
        ]

        self.error_alert.update(
            "SSH session deleted from memory."
        )

        self.refresh_sessions_panel()

    def on_button_pressed(self, event):
        button_id = event.button.id

        if button_id == "create_ssh":
            self.create_form.remove_class("hidden")
            self.error_alert.update("")

        elif button_id == "cancel_create":
            self.create_form.add_class("hidden")
            self.error_alert.update("")

        elif button_id == "manage_ssh":
            self.sessions_panel.toggle_class("hidden")
            self.refresh_sessions_panel()

        elif button_id == "submit_ssh":
            username = self.query_one(
                "#username",
                Input,
            ).value.strip()

            ssh_ip = self.query_one(
                "#ssh_ip",
                Input,
            ).value.strip()

            key_path = self.query_one(
                "#key_path",
                Input,
            ).value.strip()

            listener_port = self.query_one(
                "#listener_port",
                Input,
            ).value.strip()

            if not all([
                username,
                ssh_ip,
                key_path,
                listener_port,
            ]):
                self.error_alert.update(
                    "[bold red]All forms must be filled![/bold red]"
                )
                return

            session = {
                "id": uuid.uuid4().hex[:8],
                "username": username,
                "ssh_ip": ssh_ip,
                "key_path": key_path,
                "listener_port": listener_port,
            }

            self.sessions.append(session)

            self.start_ssh_session(session)

            self.create_form.add_class("hidden")
            self.refresh_sessions_panel()

        elif button_id.startswith("reconnect_"):
            session_id = button_id.replace(
                "reconnect_",
                "",
                1,
            )

            session = next(
                (
                    item
                    for item in self.sessions
                    if item["id"] == session_id
                ),
                None,
            )

            if session:
                self.start_ssh_session(session)
            else:
                self.error_alert.update(
                    "SSH session could not be found."
                )

        elif button_id.startswith("kill_"):
            session_id = button_id.replace(
                "kill_",
                "",
                1,
            )

            self.kill_ssh_session(session_id)

        elif button_id.startswith("delete_"):
            session_id = button_id.replace(
                "delete_",
                "",
                1,
            )

            self.delete_ssh_session(session_id)


if __name__ == "__main__":
    app = GridFlow()
    app.run(size=(80,24))

