import typer
from condor.flight_plan import get_flight_plan_path, load_flight_plan
from services.flight_plan_service import get_image_of_flight_plan

app = typer.Typer(no_args_is_help=True)


@app.command()
def preview(flightplan: str):
    fp = load_flight_plan(get_flight_plan_path(flightplan))

    image = get_image_of_flight_plan(fp)
    image.show()
