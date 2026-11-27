import json
import subprocess
from pathlib import Path
from ddgs import DDGS
import os
from session import Session


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

        return [{"type": "function", "function": tool} for tool in definitions]


# System functions


def app_list():
    directories = [
        Path("/usr/share/applications"),
        Path.home() / ".local/share/applications",
    ]

    apps = []

    for directory in directories:
        if not directory.exists():
            continue

        for file in directory.rglob("*.desktop"):
            if file.name not in apps:
                apps.append(file.name)

    return apps


def run_app(app_id, args=[]):
    if not isinstance(app_id, str) or not app_id.endswith(".desktop"):
        raise ValueError("Invalid application ID")

    directories = [
        Path("/usr/share/applications"),
        Path.home() / ".local/share/applications",
    ]

    for directory in directories:
        target = directory / app_id

        if target.is_file():
            subprocess.Popen(["gtk-launch", app_id.removesuffix(".desktop"), *args])
            return {"success": True, "app": app_id}

    raise ValueError("Application not found")


def get_volume():
    result = subprocess.run(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def set_volume(volume):
    volume = float(volume)

    if not 0 <= volume <= 150:
        raise ValueError("Volume must be between 0 and 150")

    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"], check=True
    )

    return {"success": True, "volume": volume}


def get_bright():
    result = subprocess.run(
        ["brightnessctl", "get"], capture_output=True, text=True, check=True
    )

    maximum = int(subprocess.check_output(["brightnessctl", "max"], text=True).strip())

    current = int(result.stdout.strip())

    return {"brightness": round(current / maximum * 100, 2)}


def set_bright(bright):
    bright = float(bright)

    if not 0 <= bright <= 100:
        raise ValueError("Brightness must be between 0 and 100")

    subprocess.run(["brightnessctl", "set", f"{bright}%"], check=True)

    return {"success": True, "brightness": bright}


def web_search(query, max_results=5):
    max_results = int(max_results)

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10")

    results = DDGS().text(query, max_results=max_results)

    return [
        {
            "title": item.get("title"),
            "url": item.get("href"),
            "snippet": item.get("body"),
        }
        for item in results
    ]


def ls(path):
    p = Path(path)
    if not p.exists():
        return f"No sush file or directory: {path}"

    kind = "dir" if p.is_dir() else "file"
    return path if kind == "file" else [f for f in p.iterdir()]


def write_file(path, content=""):
    try:
        file = open(path, "w")
        file.write(content)
        file.close()
        return 0
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_file(path):
    try:
        file = open(path)
        content = file.read()
        file.close()
        return {"content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


def mkdir(path):
    try:
        return Path(path).mkdir()
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_user_data(key: str = None):
    path = Path.home() / ".agent" / "user_data.json"

    try:
        if not path.exists():
            return {"success": False, "error": "User data file does not exist"}

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if key:
            return {"success": key in data, "key": key, "value": data.get(key)}

        return {"success": True, "data": data}

    except (OSError, json.JSONDecodeError) as e:
        return {"success": False, "error": str(e)}


def save_user_data(data: dict):
    path = Path.home() / ".agent" / "user_data.json"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                oldjs = json.load(f)
        else:
            oldjs = {}

        oldjs.update(data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(oldjs, f, ensure_ascii=False, indent=4)

        return {"success": True, "path": str(path)}

    except (OSError, json.JSONDecodeError) as e:
        return {"success": False, "error": str(e)}


def set_session_info(name: str, id: str):
    Session.session_id = id
    Session.session_name = name
    return {"success": True}


import glob, vdf


def steam_games_list():
    res = []
    for file in glob.glob(
        os.path.expanduser("~/.steam/steam/userdata/*/config/shortcuts.vdf")
    ):
        with open(file, "rb") as f:
            data = vdf.binary_load(f)

        for game in data.get("shortcuts", {}).values():
            res.append(
                {
                    "name": game.get("AppName", "<unknown>"),
                    "appid": str(((game.get("appid", 0) & 0xFFFFFFFF) << 32) | 0x02000000)
                }
            )
    print(f"Steam Games:\n{res}")
    return res


def run_steam_game(app_id: str):
    subprocess.run(["steam", f"steam://rungameid/{app_id}"],check=False)
    print(f"Open Game: {app_id}")


# Register tools

registry = ToolRegistry()

registry.register("get_volume", get_volume)
registry.register("set_volume", set_volume)
registry.register("get_bright", get_bright)
registry.register("set_bright", set_bright)
registry.register("app_list", app_list)
registry.register("run_app", run_app)
registry.register("web_search", web_search)
registry.register("write_file", write_file)
registry.register("read_file", read_file)
registry.register("ls", ls)
registry.register("mkdir", mkdir)
registry.register("save_user_data", save_user_data)
registry.register("read_user_data", read_user_data)
registry.register("set_session_info", set_session_info)
registry.register("run_steam_game", run_steam_game)
registry.register("steam_games_list", steam_games_list)
