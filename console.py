import typer
from rich import print
from commands.flight_plan_command import app as flight_plan_commands

app = typer.Typer(no_args_is_help=True)
app.add_typer(flight_plan_commands, name="flight-plan")


@app.command()
def placeholder(flightplan: str):
    print("[yellow]placeholder for later usage[/yellow]")


if __name__ == "__main__":
    app()
