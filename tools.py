
import json
import subprocess
from pathlib import Path
from ddgs import DDGS

class ToolRegistry:
    def __init__(self):
        self.handlers = {}

    def register(self, name, handler):
        self.handlers[name] = handler

    def execute(self, name, arguments):
        try:
            handler = self.handlers.get(name)

            if handler is None:
                raise ValueError(f"Unknown tool: {name}")

            return handler(**arguments)
        except Exception as ex:
            print(f"Failed to execute tool {name}: {ex}")

    def definitions(self, path="tool_def.json"):
        with open(path, "r", encoding="utf-8") as f:
            definitions = json.load(f)

        return [
            {
                "type": "function",
                "function": tool
            }
            for tool in definitions
        ]


# System functions


def app_list():
    directories = [
        Path("/usr/share/applications"),
        Path.home() / ".local/share/applications"
    ]

    apps = []

    for directory in directories:
        if not directory.exists():
            continue

        for file in directory.rglob("*.desktop"):
            if file.name not in apps:
                apps.append(file.name)

    return apps


def run_app(app_id):
    if not isinstance(app_id, str) or not app_id.endswith(".desktop"):
        raise ValueError("Invalid application ID")

    directories = [
        Path("/usr/share/applications"),
        Path.home() / ".local/share/applications"
    ]

    for directory in directories:
        target = directory / app_id

        if target.is_file():
            subprocess.Popen(
                ["gtk-launch", app_id.removesuffix(".desktop")]
            )
            return {"success": True, "app": app_id}

    raise ValueError("Application not found")


def get_volume():
    result = subprocess.run(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
        capture_output=True,
        text=True,
        check=True
    )

    return result.stdout.strip()


def set_volume(volume):
    volume = float(volume)

    if not 0 <= volume <= 150:
        raise ValueError("Volume must be between 0 and 150")

    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"],
        check=True
    )

    return {"success": True, "volume": volume}


def get_bright():
    result = subprocess.run(
        ["brightnessctl", "get"],
        capture_output=True,
        text=True,
        check=True
    )

    maximum = int(subprocess.check_output(
        ["brightnessctl", "max"],
        text=True
    ).strip())

    current = int(result.stdout.strip())

    return {"brightness": round(current / maximum * 100, 2)}


def set_bright(bright):
    bright = float(bright)

    if not 0 <= bright <= 100:
        raise ValueError("Brightness must be between 0 and 100")

    subprocess.run(
        ["brightnessctl", "set", f"{bright}%"],
        check=True
    )

    return {"success": True, "brightness": bright}


def web_search(query, max_results=5):
    max_results = int(max_results)

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10")

    results = DDGS().text(
        query,
        max_results=max_results
    )

    return [
        {
            "title": item.get("title"),
            "url": item.get("href"),
            "snippet": item.get("body")
        }
        for item in results
    ]



# Register tools

registry = ToolRegistry()

registry.register("get_volume", get_volume)
registry.register("set_volume", set_volume)
registry.register("get_bright", get_bright)
registry.register("set_bright", set_bright)
registry.register("app_list", app_list)
registry.register("run_app", run_app)
registry.register("web_search", web_search)