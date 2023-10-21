import builtins
import readline
import rlcompleter
import sys
import urllib.parse
from code import InteractiveConsole
from typing import Annotated, Optional

import bson
import bson.json_util
import pymongo.cursor
import pymongo.results
import typer
from pymongo import MongoClient


def cli(url: Annotated[Optional[str], typer.Argument()] = None):
    context = {}

    if url is not None:
        pieces = urllib.parse.urlparse(url)
        default_database_name = pieces.path.removeprefix("/")

        if default_database_name == "":
            default_database_name = "test"

        client = MongoClient(url)
        context["db"] = client.get_database(default_database_name)
    else:
        context["db"] = None

    def use(db_name: str):
        context["db"] = context["db"].client.get_database(db_name)
        return context["db"]

    def print_result():
        hasattr(builtins, "_")

    original_display_hook = sys.displayhook

    def displayhook(value):
        if isinstance(value, pymongo.cursor.Cursor):
            max_page_size = context.get("MDBPYSH_MAX_PAGE_SIZE", 20)
            output_format = context.get("MDBPYSH_OUTPUT_FORMAT", "repr")
            json_options = context.get("MDBPYSH_OUTPUT_JSON_OPTIONS", bson.json_util.JSONOptions())
            json_indent = context.get("MDBPYSH_OUTPUT_JSON_INDENT", None)

            count = 0
            while count < max_page_size:
                try:
                    doc = value.next()
                except StopIteration:
                    break
                count += 1

                if output_format == "json":
                    sys.stdout.write(bson.json_util.dumps(doc, json_options=json_options, indent=json_indent))
                else:
                    sys.stdout.write(repr(doc))
                sys.stdout.write("\n")

            sys.stdout.write(f"(Returned {count} documents)\n")

            if not value.alive:
                sys.stdout.write("(Cursor exhausted)\n")
            
            builtins._ = value
            return

        if isinstance(value, pymongo.results._WriteResult):
            if isinstance(value, pymongo.results.InsertOneResult):
                text = repr({"acknowledge": value.acknowledged, "inserted_id": value.inserted_id})
            else:
                text = repr(value.raw_result)

            sys.stdout.write(text)
            sys.stdout.write("\n")
            builtins._ = value
            return
        
        original_display_hook(value)

    context.setdefault("MDBPYSH_MAX_PAGE_SIZE", 20)
    context.setdefault("MDBPYSH_OUTPUT_FORMAT", "repr")

    context["bson"] = bson
    context["use"] = use
    context["print_result"] = print_result
    context["pr"] = print_result

    sys.displayhook = displayhook

    readline.set_completer(rlcompleter.Completer(context).complete)

    # https://stackoverflow.com/questions/7116038/python-repl-tab-completion-on-macos
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    console = InteractiveConsole(locals=context)
    console.interact(banner="MongoDB Python Shell")


def main():
    typer.run(cli)

if __name__ == "__main__":
    main()
