import math
import urllib.parse
from typing import Optional, Union
from rich.table import Table

import bson
import bson.json_util
import pymongo.cursor
import pymongo.command_cursor
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure


def format_bytes(bytes_value: int):
    if bytes_value < 1024:
        return "{: 7.0f}   B".format(bytes_value)

    if bytes_value / math.pow(1024, 1) < 1024:
        return "{: 7.2f} KiB".format(bytes_value / math.pow(1024, 1))

    if bytes_value / math.pow(1024, 2) < 1024:
        return "{: 7.2f} MiB".format(bytes_value / math.pow(1024, 2))

    if bytes_value / math.pow(1024, 3) < 1024:
        return "{: 7.2f} GiB".format(bytes_value / math.pow(1024, 3))

    return "{: 7.2f} TiB".format(bytes_value / math.pow(1024, 4))


def format_si(qty):
    if qty < 1000:
        return "{: 7.0f}  ".format(qty)

    if qty / math.pow(1000, 1) < 1000:
        return "{: 7.2f} K".format(qty / math.pow(1000, 1))

    if qty / math.pow(1000, 2) < 1000:
        return "{: 7.2f} M".format(qty / math.pow(1000, 2))

    if qty / math.pow(1000, 3) < 1000:
        return "{: 7.2f} G".format(qty / math.pow(1000, 3))

    return "{: 7.2f} T".format(qty / math.pow(1000, 4))


def show_dbs(ctx):
    db: Optional[Database] = ctx["db"]

    if db is None:
        raise Exception("No default connection")

    result = db.client.get_database("admin").command("listDatabases")

    table = Table()
    table.add_column("NAME", justify="left")
    table.add_column("DISK SIZE", justify="right")

    for it in result["databases"]:
        table.add_row(it["name"], format_bytes(it["sizeOnDisk"]))

    ctx["console"].print(table)


def connect(url):
    pieces = urllib.parse.urlparse(url)
    default_database_name = pieces.path.removeprefix("/")

    if default_database_name == "":
        default_database_name = "test"

    client = MongoClient(url)
    return client.get_database(default_database_name)


def use(ctx, db_name: str):
    ctx["db"] = ctx["db"].client.get_database(db_name)
    return ctx["db"]


BYTESTRING_MAX_LENGTH = 8
NUMSTRING_MAX_LENGTH = 8
DEFAULT_LIMIT = 4
COLLECTION_TYPE_PAD_LENGTH = len("collection")
SI_STR_PADSIZE = 9
BYTES_STR_PADSIZE = 11
INDEXES_PAD_LENGTH = len("INDEXES")


def show_collections(ctx: dict, db_name: Optional[str] = None, system: bool = False):
    db: Database = ctx["db"]

    if db_name is not None:
        db = db.client.get_database(db_name)

    collectionInfos = list(db.list_collections())

    max_name = 0
    for it in collectionInfos:
        max_name = max(max_name, len(it["name"]))

    table = Table()

    table.add_column("NAME", justify="left")
    table.add_column("TYPE", justify="left")
    table.add_column("COUNT", justify="right")
    table.add_column("SIZE", justify="right")
    table.add_column("STORAGE", justify="right")
    table.add_column("OBJ SIZE", justify="right")
    table.add_column("INDEXES", justify="right")
    table.add_column("INDEXES SIZE", justify="right")

    collectionInfos.sort(key=lambda it: it["name"])

    for it in collectionInfos:
        if it["name"].startswith("system.") and not system:
            continue

        if it["type"] == "view":
            table.add_row(it["name"], it["type"])
            continue

        try:
            stats = db.get_collection(it["name"]).aggregate(
                [{"$collStats": {"storageStats": {"scale": 1}}}]
            )
        except OperationFailure as ex:
            print(f"No {it['name']}: {ex}")
            continue

        stats = next(stats)["storageStats"]

        table.add_row(
            it["name"],
            it["type"],
            format_si(stats["count"]) if "count" in stats else "N/A",
            format_bytes(stats["size"]),
            format_bytes(stats["storageSize"]),
            format_bytes(stats["avgObjSize"]),
            format_si(stats["nindexes"]),
            format_bytes(stats["totalIndexSize"]),
        )

    ctx["console"].print(table)


def printcur(
    context: dict,
    cur: Union[pymongo.cursor.Cursor, pymongo.command_cursor.CommandCursor],
):
    max_page_size = context.get("MONGOPYSH_MAX_PAGE_SIZE", 20)
    output_format = context.get("MONGOPYSH_OUTPUT_FORMAT", "repr")
    json_options = context.get(
        "MONGOPYSH_OUTPUT_JSON_OPTIONS", bson.json_util.JSONOptions()
    )
    json_indent = context.get("MONGOPYSH_OUTPUT_JSON_INDENT", None)

    count = 0
    while count < max_page_size:
        try:
            doc = cur.next()
        except StopIteration:
            break
        count += 1

        if output_format == "json":
            context["console"].print(
                bson.json_util.dumps(doc, json_options=json_options, indent=json_indent)
            )
        else:
            context["console"].print(repr(doc))

    context["console"].print(f"(Returned {count} documents)")

    if not cur.alive:
        context["console"].print("(Cursor exhausted)")
