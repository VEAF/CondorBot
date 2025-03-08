from discord import ui, Member, SelectOption, Interaction
from condor.flight_plan import list_flight_plans


class SelectFlightPlanView(ui.View):
    def __init__(self, user: Member):
        super().__init__()
        self.user = user
        self.response = None  # Stocke la sélection

    @ui.select(
        placeholder="Select a flight plan...",
        min_values=1,
        max_values=1,
        options=[
            SelectOption(
                label=fp.human_filename, value=fp.filename, description=f"{fp.landscape} - {fp.distance / 1000:.0f} km"
            )
            for fp in list_flight_plans()
        ],
    )
    async def select_callback(self, interaction: Interaction, select: ui.Select):
        if interaction.user != self.user:
            return await interaction.response.send_message("You are not granted to answer !", ephemeral=True)
        self.response = select.values[0]
        await interaction.response.send_message(f"✅ Flight plan selected : {self.response}", ephemeral=True)
        self.stop()
