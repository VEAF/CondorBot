from abc import abstractmethod
from discord import ui, Member, SelectOption, Interaction
from discord.integrations import MISSING
from condor.flight_plan import flight_plan_to_markdown, get_flight_plan_path, list_flight_plans, load_flight_plan


async def send_response(
    interaction: Interaction,
    content: str,
    *,
    ephemeral: bool = True,
    channel_message: bool = False,
    delete_after: float | None = None,
    view: ui.View | None = MISSING,
    follow_up: bool = False,
) -> None:
    """Send a response either ephemerally via the interaction or publicly via the channel."""
    if channel_message:
        await interaction.channel.send(content)
    elif follow_up:
        await interaction.followup.send(content, ephemeral=True, username=interaction.user.display_name)
    else:
        await interaction.response.send_message(content, ephemeral=ephemeral, delete_after=delete_after, view=view)


async def handle_error(interaction: Interaction, error_msg: str) -> None:
    """Simple private reponse to advise error in commands"""
    await send_response(interaction, f"❌ {error_msg}", ephemeral=True)


def select_flight_plans_from_list() -> ui.Select:
    return ui.Select(
        placeholder="Select a flight plan...",
        min_values=1,
        max_values=1,
        options=[
            SelectOption(
                label=fp.human_filename,
                value=fp.filename,
                description=f"{fp.landscape} - {fp.distance / 1000:.0f} km",
            )
            for fp in list_flight_plans()
        ],
    )


class SelectFlightPlanViewAbstract(ui.View):
    def __init__(self, user: Member):
        super().__init__()
        self.user = user
        self.response: str | None = None

        self.select_menu = select_flight_plans_from_list()
        self.select_menu.callback = self.select_callback
        self.add_item(self.select_menu)

    @abstractmethod
    async def select_callback(self, interaction: Interaction): ...


class SelectStartFlightPlan(SelectFlightPlanViewAbstract):
    async def select_callback(self, interaction: Interaction):
        if interaction.user != self.user:
            return send_response(interaction, "You are not granted to answer !")
        self.response = self.select_menu.values[0]
        await send_response(interaction, "done", delete_after=1)
        self.stop()


class SelectViewFlightPlan(SelectFlightPlanViewAbstract):
    async def select_callback(self, interaction: Interaction):
        if interaction.user != self.user:
            return send_response(interaction, "You are not granted to answer !")
        self.response = self.select_menu.values[0]

        flight_plan = load_flight_plan(get_flight_plan_path(self.response))

        # remove original message
        await interaction.response.defer()
        await interaction.delete_original_response()

        await interaction.followup.send(flight_plan_to_markdown(flight_plan), ephemeral=True)
        self.stop()
