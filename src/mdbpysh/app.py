import functools
import readline
import rlcompleter
import sys
from code import InteractiveConsole
from types import CodeType
from typing import Annotated, Any, Optional

import bson
import bson.json_util
import mdbpysh.extensions
import mdbpysh.shell
import rich.console
import rich.pretty
import rich.protocol
import rich.repr
import typer
from mdbpysh.helpers import connect, printcur, show_collections, show_dbs, use


class MongoPyShell(InteractiveConsole):
    def runcode(self, code: CodeType) -> None:
        sys.ps1 = self.locals["prompt"]()
        return super().runcode(code)


def cli(url: Annotated[Optional[str], typer.Argument()] = None):
    mdbpysh.extensions.apply()

    console = rich.console.Console()

    context: dict[str, Any] = {"console": console}

    context.setdefault("MDBPYSH_DISPLAY_RESULTS", True)
    context.setdefault("MDBPYSH_MAX_PAGE_SIZE", 20)
    context.setdefault("MDBPYSH_OUTPUT_FORMAT", "repr")
    context.setdefault("MDBPYSH_OUTPUT_JSON_OPTIONS", bson.json_util.JSONOptions())
    context.setdefault("MDBPYSH_OUTPUT_JSON_INDENT", None)

    context["bson"] = bson

    context["print"] = console.print
    context["pprint"] = rich.pretty.pprint

    context["use"] = functools.partial(use, context)
    context["connect"] = functools.partial(connect)
    context["show_dbs"] = functools.partial(show_dbs, context)
    context["show_collections"] = functools.partial(show_collections, context)

    context["printcur"] = functools.partial(printcur, context)
    context["pc"] = context["printcur"]

    sys.displayhook = functools.partial(mdbpysh.shell.displayhook, context)

    context["prompt"] = functools.partial(mdbpysh.shell.default_prompt, context)

    readline.set_completer(rlcompleter.Completer(context).complete)

    # https://stackoverflow.com/questions/7116038/python-repl-tab-completion-on-macos
    if readline.__doc__ and ("libedit" in readline.__doc__):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    if url is not None:
        db = connect(url)

        data = db.client.server_info()

        console.print(f"Using MongoDB: {data['version']}")

        context["db"] = db
    else:
        context["db"] = None

    shell = MongoPyShell(locals=context)

    # TODO: Load RC

    sys.ps1 = context["prompt"]()

    shell.interact(banner="MongoDB Python Shell")


def main():
    typer.run(cli)


if __name__ == "__main__":
    main()
