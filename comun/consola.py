"""Salida uniforme para los siete scripts del pipeline."""

from __future__ import annotations

import sys

from rich.console import Console

_con = Console()
_err = Console(stderr=True)


def titulo(paso: str, texto: str) -> None:
    _con.rule(f"[bold cyan]{paso}[/] · {texto}")


def info(texto: str) -> None:
    _con.print(texto)


def ok(texto: str) -> None:
    _con.print(f"[green]✓[/] {texto}")


def aviso(texto: str) -> None:
    _con.print(f"[yellow]![/] {texto}")


def error(texto: str) -> None:
    _err.print(f"[bold red]✗[/] {texto}")


def abortar(texto: str, codigo: int = 1) -> None:
    """Imprime el motivo y corta la ejecución.

    Los scripts prefieren abortar antes que producir un video incompleto.
    """
    error(texto)
    sys.exit(codigo)


def siguiente(comando: str) -> None:
    _con.print(f"\n[dim]Paso siguiente:[/] [bold]{comando}[/]")
