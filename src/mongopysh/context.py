import typing
from types import FunctionType
from typing import Optional, Union

from pymongo.database import Database
from rich.console import Console

MONGOPYSH_DISPLAY_RESULTS = "MONGOPYSH_DISPLAY_RESULTS"
MONGOPYSH_MAX_PAGE_SIZE = "MONGOPYSH_MAX_PAGE_SIZE"
MONGOPYSH_OUTPUT_FORMAT = "MONGOPYSH_OUTPUT_FORMAT"
MONGOPYSH_OUTPUT_JSON_OPTIONS = "MONGOPYSH_OUTPUT_JSON_OPTIONS"
MONGOPYSH_OUTPUT_JSON_INDENT = "MONGOPYSH_OUTPUT_JSON_INDENT"


class Context(typing.Protocol):
    def set(self, key: str, value):
        ...

    @property
    def dict(self) -> dict:
        ...

    @property
    def console(self) -> Console:
        ...

    @property
    def db(self) -> Optional[Database]:
        ...

    @property
    def prompt(self) -> FunctionType:
        ...

    def get_flag(self, flag) -> Union[int, str, bool]:
        ...
