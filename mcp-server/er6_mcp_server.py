#!/usr/bin/env python3
"""MCP server exposing SAP ER6 system via sapcli (read-only)."""

import asyncio
import os
import subprocess

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

CONDA_ENV = "sapcli-env"
ENV_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".sapcli.env")
)


def _sapcli_env() -> dict:
    """Merge ER6 connection vars from .sapcli.env into current environment."""
    env = os.environ.copy()
    if not os.path.exists(ENV_FILE):
        return env
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith("export "):
                key, _, val = line[7:].partition("=")
                env[key.strip()] = val.strip().strip("'\"")
    return env


def _run(args: list[str], timeout: int = 60) -> str:
    """Run sapcli inside the conda env and return stdout."""
    cmd = ["conda", "run", "--no-capture-output", "-n", CONDA_ENV, "sapcli"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_sapcli_env(),
    )
    if result.returncode != 0:
        err = result.stderr.strip() or f"sapcli exited with code {result.returncode}"
        raise RuntimeError(err)
    return result.stdout.strip()


app = Server("er6-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="query_sql",
            description=(
                "Run a read-only ABAP Open SQL SELECT against SAP system ER6. "
                "Use '--rows N' to limit result size (default 100, max 5000). "
                "ABAP Open SQL dialect: no JOINs, no subqueries, "
                "use UP TO N ROWS inline or rely on the rows parameter."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "ABAP Open SQL SELECT statement",
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Maximum rows to return (default 100)",
                        "default": 100,
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="read_table_def",
            description=(
                "Read the DDIC transparent table or structure definition "
                "(CDS-style DDL source) from ER6. "
                "Example: APS_IAM_W_APP, TADIR, USR02."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Table or structure name (uppercase)",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="read_cds_view",
            description=(
                "Read the CDS view source (DDLS object) from ER6. "
                "Use TADIR to find CDS view names first "
                "(OBJECT = 'DDLS', OBJ_NAME LIKE 'APS_IAM%')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "CDS view/DDLS object name (uppercase)",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="read_class",
            description="Read the ABAP class source from ER6.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Class name, e.g. CL_APS_IAM_BROLE_RLDEPO",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="read_program",
            description="Read an ABAP program or report source from ER6.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Program/report name (uppercase)",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_package",
            description=(
                "List all repository objects in an ABAP package in ER6. "
                "Example packages: CLOUD_FI_TR_IAM, APS_IAM."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Package name (uppercase)",
                    },
                },
                "required": ["name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "query_sql":
            rows = int(arguments.get("rows", 100))
            rows = min(rows, 5000)
            output = _run(
                ["datapreview", "osql", arguments["sql"], "--rows", str(rows)]
            )

        elif name == "read_table_def":
            output = _run(["table", "read", arguments["name"].upper()])

        elif name == "read_cds_view":
            output = _run(["ddl", "read", arguments["name"].upper()])

        elif name == "read_class":
            output = _run(["class", "read", arguments["name"].upper()])

        elif name == "read_program":
            output = _run(["program", "read", arguments["name"].upper()])

        elif name == "list_package":
            output = _run(["package", "list", arguments["name"].upper()])

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=output or "(no output)")]

    except Exception as exc:
        return [types.TextContent(type="text", text=f"ERROR: {exc}")]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
