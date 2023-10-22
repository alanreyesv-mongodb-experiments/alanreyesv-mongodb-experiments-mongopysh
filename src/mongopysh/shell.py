import code
import codeop
import os
import sys
from code import InteractiveConsole
from typing import Union

import pymongo.command_cursor
import pymongo.cursor
import pymongo.results
from pymongo import MongoClient
from pymongo.server_type import SERVER_TYPE
from pymongo.topology_description import TOPOLOGY_TYPE

from types import CodeType

from pymongo.topology_description import TopologyDescription

from mongopysh.context import MONGOPYSH_DISPLAY_RESULTS, Context
from mongopysh.helpers import printcur


class MongoPyShell(InteractiveConsole):
    def __init__(self, context: Context) -> None:
        self.initializing = True
        self.context = context
        super().__init__(locals=context.dict)

    def runcode(self, code: CodeType) -> None:
        super().runcode(code)
        sys.ps1 = self.context.prompt()

    def showsyntaxerror(self, filename: Union[str, None] = None) -> None:
        self.context.console.print_exception(suppress=[code, codeop])
        if self.initializing:
            self.context.console.print("Error running .mongopyshrc file")
            raise SystemExit()

    def showtraceback(self) -> None:
        self.context.console.print_exception(suppress=[code, codeop])
        if self.initializing:
            self.context.console.print("Error running .mongopyshrc file")
            raise SystemExit()

    def loadrc(self):
        rc_path = os.path.expanduser("~/.mongopyshrc.py")

        if not os.path.exists(rc_path):
            return

        with open(rc_path) as fp:
            script = fp.readlines()

        requires_more_input = False

        for line in script:
            requires_more_input = self.push(line)

        self.initializing = False

        if requires_more_input:
            self.resetbuffer()
            self.context.console.print("Incomplete command in .mongopyshrc.py")

    def write(self, data):
        self.context.console.print(data, end="")


def displayhook(ctx: Context, value):
    if value is None:
        return

    console = ctx.console

    # Prevent infinite recursion?
    ctx.set("_", None)

    display_results = ctx.get_flag(MONGOPYSH_DISPLAY_RESULTS)

    if isinstance(value, pymongo.cursor.Cursor) or isinstance(
        value, pymongo.command_cursor.CommandCursor
    ):
        if display_results:
            printcur(ctx, value)
        else:
            console.print(value)

        ctx.set("it", value)

    elif isinstance(value, pymongo.results._WriteResult):
        ctx.set("res", value)
    else:
        console.print(value)

    ctx.set("_", value)


def getDefaultPromptPrefix() -> str:
    """
    const extraConnectionInfo = this.connectionInfo?.extraInfo;

    if (extraConnectionInfo?.is_data_federation) {
      return 'AtlasDataFederation';
    } else if (extraConnectionInfo?.is_local_atlas) {
      return 'AtlasLocalDev';
    } else if (extraConnectionInfo?.is_atlas) {
      return 'Atlas';
    } else if (
      extraConnectionInfo?.is_enterprise ||
      this.connectionInfo?.buildInfo?.modules?.indexOf('enterprise') >= 0
    ) {
      return 'Enterprise';
    }
    """

    return ""


def getTopologySinglePrompt(description: TopologyDescription):
    if len(description.known_servers) != 1:
        return (None, None)

    server = description.known_servers[0]

    if server.server_type == SERVER_TYPE.Mongos:
        serverType = "mongos"
    elif server.server_type == SERVER_TYPE.RSPrimary:
        serverType = "primary"
    elif server.server_type == SERVER_TYPE.RSSecondary:
        serverType = "secondary"
    elif server.server_type == SERVER_TYPE.RSArbiter:
        serverType = "arbiter"
    elif server.server_type == SERVER_TYPE.RSOther:
        serverType = "other"
    else:
        ## Standalone, PossiblePrimary, RSGhost, LoadBalancer, Unknown
        serverType = ""

    return (
        server.replica_set_name,
        serverType,
    )


def getTopologySpecificPrompt(client: MongoClient):
    # TODO: once a driver with NODE-3011 is available set type to TopologyDescription
    description = client.topology_description

    if description is None:
        return ""

    replicaSet = description.replica_set_name
    serverTypePrompt = ""

    # TODO: replace with proper TopologyType constants - NODE-2973

    if description.topology_type == TOPOLOGY_TYPE.Single:
        replicaSet, serverType = getTopologySinglePrompt(description)
        serverTypePrompt = f"[direct: {serverType}]" if serverType else ""
    elif description.topology_type == TOPOLOGY_TYPE.ReplicaSetNoPrimary:
        serverTypePrompt = "[secondary]"

    elif description.topology_type == TOPOLOGY_TYPE.ReplicaSetWithPrimary:
        serverTypePrompt = "[primary]"

    elif description.topology_type == TOPOLOGY_TYPE.Sharded:
        serverTypePrompt = "[mongos]"

    else:
        return ""

    setNamePrefix = f"{replicaSet} " if replicaSet else ""

    return f"{setNamePrefix}{serverTypePrompt}"


def default_prompt(ctx: Context):
    db = ctx.db

    # if (this.connectionInfo?.extraInfo?.is_stream) {
    #  return 'AtlasStreamProcessing> ';
    # }

    prefix = getDefaultPromptPrefix()

    if db is not None:
        topologyInfo = getTopologySpecificPrompt(db.client)
        dbname = db.name
    else:
        topologyInfo = ""
        dbname = ""

    pieces = " ".join(filter(lambda it: it, [prefix, topologyInfo, dbname]))

    return f"{pieces}> "
