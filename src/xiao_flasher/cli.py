"""CLI entry point for xiao-flasher."""

import click


@click.command()
def main() -> None:
    """XIAO-RP2040 Firmware Flashing CLI."""
    click.echo("xiao-flash initialized.")


if __name__ == "__main__":
    main()
