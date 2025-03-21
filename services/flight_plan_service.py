from PIL import Image, ImageDraw
from rich import print
from condor.flight_plan import FlightPlan, get_landscape_image_filepath

IMAGE_BORDER_PIXELS = 50
FLIGHT_PLAN_PATH_COLOR = (255, 0, 0)


def transpose_map_xy(image_size: tuple[int, int], x: float, y: float) -> tuple[int, int]:
    return ((image_size[0] - 1 - int(x / 90)), image_size[1] - 1 - int(y / 90))


def get_image_of_flight_plan(flight_plan: FlightPlan) -> Image:
    image = Image.open(get_landscape_image_filepath(flight_plan.landscape))

    draw = ImageDraw.Draw(image)

    points = [transpose_map_xy(image.size, tp.pos_x, tp.pos_y) for tp in flight_plan.turnpoints]

    draw.line(points, width=5, fill=FLIGHT_PLAN_PATH_COLOR)

    area = (
        max(min(p[0] for p in points) - IMAGE_BORDER_PIXELS, 0),
        max(min(p[1] for p in points) - IMAGE_BORDER_PIXELS, 0),
        min(max(p[0] for p in points) + IMAGE_BORDER_PIXELS, image.size[0] - 1),
        min(max(p[1] for p in points) + IMAGE_BORDER_PIXELS, image.size[1] - 1),
    )

    return image.crop(area)
