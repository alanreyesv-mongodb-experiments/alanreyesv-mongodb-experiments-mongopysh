import functools
import readline
import rlcompleter
import sys
from types import FunctionType
from typing import Annotated, Optional

import bson
import bson.json_util
from pymongo.database import Database
from mongopysh.context import (
    Context,
    MONGOPYSH_DISPLAY_RESULTS,
    MONGOPYSH_MAX_PAGE_SIZE,
    MONGOPYSH_OUTPUT_FORMAT,
    MONGOPYSH_OUTPUT_JSON_INDENT,
    MONGOPYSH_OUTPUT_JSON_OPTIONS,
)
import mongopysh.extensions
import mongopysh.shell
import rich.console
import rich.pretty
import rich.protocol
import rich.repr
import typer
from mongopysh.helpers import connect, printcur, show_collections, show_dbs, use

DEFAULTS = {
    MONGOPYSH_DISPLAY_RESULTS: True,
    MONGOPYSH_MAX_PAGE_SIZE: 20,
    MONGOPYSH_OUTPUT_FORMAT: "repr",
    MONGOPYSH_OUTPUT_JSON_OPTIONS: bson.json_util.JSONOptions(),
    MONGOPYSH_OUTPUT_JSON_INDENT: None,
}


class ShellContext(Context):
    def __init__(self) -> None:
        console = rich.console.Console()
        self._dict = {
            "console": console,
            "bson": bson,
            "print": console.print,
            "use": functools.partial(use, self),
            "connect": functools.partial(connect),
            "show_dbs": functools.partial(show_dbs, self),
            "show_collections": functools.partial(show_collections, self),
            "printcur": functools.partial(printcur, self),
            "prompt": functools.partial(mongopysh.shell.default_prompt, self),
        }

        self._dict.update(DEFAULTS)

    def set(self, key, value):
        self._dict[key] = value

    @property
    def dict(self):
        return self._dict

    @property
    def console(self) -> rich.console.Console:
        return self._dict["console"]

    @property
    def db(self) -> Optional[Database]:
        return self._dict.get("db")

    @property
    def prompt(self) -> FunctionType:
        return self._dict["prompt"]

    def get_flag(self, flag):
        return self._dict.get(flag, DEFAULTS[flag])


def cli(url: Annotated[Optional[str], typer.Argument()] = None):
    mongopysh.extensions.apply()

    context = ShellContext()

    sys.displayhook = functools.partial(mongopysh.shell.displayhook, context)
    readline.set_completer(rlcompleter.Completer(context.dict).complete)

    # https://stackoverflow.com/questions/7116038/python-repl-tab-completion-on-macos
    if readline.__doc__ and ("libedit" in readline.__doc__):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    if url is None:
        url = "mongodb://localhost:27017/test?directConnection=true"

    if url is not None:

        db = connect(url)

        data = db.client.server_info()

        context.console.print(f"Using MongoDB: {data['version']}")

        context.set("db", db)
    else:
        context.set("db", None)

    shell = mongopysh.shell.MongoPyShell(context)

    shell.loadrc()

    sys.ps1 = context.prompt()

    shell.interact(banner="MongoDB Python Shell")


def main():
    typer.run(cli)


if __name__ == "__main__":
    main()
