# MongoDB Python Shell

The new Mongo Shell `mongosh` is... weird...mostly because its
JavaScript.

Python being also a dynamic language that also support a very similar
object notation but more strict with types, may be a good candidate for
an alternate shell.

This is an experiment to do so.

## Installation

Install with `pip`:

```bash
pip install git+https://github.com/alanreyesv-mongodb-experiments/mongopysh.git
```

Also compatible and recomended to use [`pipx`](https://pypa.github.io/pipx/):

```bash
pipx install git+https://github.com/alanreyesv-mongodb-experiments/mongopysh.git
```

## Usage

```bash
mongopysh [connection string]
```

## Helpers

Being a Python shell, all commands must be valid Python commands so
there is no `show dbs`, `show collections` or `use dbname` syntax.
Instead use:

```python
show_dbs()
show_collections()
use("dbname")
```

Running queries should use Python driver notation:

```python
db.find_one({"field": "value"})
db.insert_one({"field": "value"})
```

Use `it` to read the next batch of results:

```python
it
```

Actually, `it` is a reference to the cursor. Using a cursor as command
will read the next batch of results.

To disable this behaviour set the `MONGOPYSH_DISPLAY_RESULTS` to `False`:

```python
MONGOPYSH_DISPLAY_RESULTS = False
```

Then, cursors will no longer read data automatically.

To trigger manually the behavior of reading from the cursor use:

```python
printcur(cursor)
```

To display the query results in [Extended JSON](https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/) format use:

```python
# Default value is "repl"
MONGOPYSH_OUTPUT_FORMAT = "json"
```

For pretty JSON output, set the `MONGOPYSH_OUTPUT_JSON_INDENT` to the
number of spaces to indent subsequent lines:

```python
MONGOPYSH_OUTPUT_JSON_INDENT = 2
```

All this options and other initialization code can be set in the
`.mongopyshrc.py` file.
