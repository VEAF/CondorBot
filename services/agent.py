import os
from discord import Interaction, Message, Attachment
from condor.config import get_config
from condor.flight_plan import FlightPlan, flight_plan_to_markdown, list_flight_plans, load_flight_plan
from condor.server_manager import get_server_status, OnlineStatus

SERVER_STATUS_ICONS = {
    OnlineStatus.OFFLINE: "❌",
    OnlineStatus.NOT_RUNNING: "💿",
    OnlineStatus.JOINING_ENABLED: "🕑",
    OnlineStatus.RACE_IN_PROGRESS: "✈️",
    OnlineStatus.JOINING_DISABLED: "🛬",
}


async def on_flight_plan_upload(message: Message, attachment: Attachment) -> None:
    file_name = attachment.filename

    print(f"a new flight plan was received: {file_name}")

    local_filepath = f"{get_config().flight_plans_path}/{file_name}"
    await attachment.save(local_filepath)

    try:
        flight_plan = load_flight_plan(local_filepath)

        msg = f"✅ {message.author} has uploaded a new flight plan:\n\n"
        msg += flight_plan_to_markdown(flight_plan)

        print(f"✅ flight plan [blue]{file_name}[/blue] [green]saved[/green]")
        await message.channel.send(msg)

    except Exception as exc:
        os.remove(local_filepath)
        print(f"❌ flight plan [blue]{file_name}[/blue] [red]ignored[/red]")
        await message.channel.send(f"your flight plan is refused: {exc}")


async def on_files_upload(message: Message) -> None:
    for attachment in message.attachments:
        extension = ".fpl"
        if attachment.filename.endswith(extension):
            await on_flight_plan_upload(message, attachment)


async def on_list_flight_plans(interaction: Interaction) -> None:
    fpl = list_flight_plans()
    msg = f"{'✅' if len(fpl) > 0 else '❌'} {len(fpl)} flight plans available:\n\n"
    for fp in fpl:
        msg += f"- {os.path.basename(fp.filename)} *{fp.landscape} - {fp.distance / 1000:.0f} km*\n"

    await interaction.response.send_message(msg, ephemeral=True)


async def on_status(interaction: Interaction) -> None:
    try:
        status, _ = get_server_status()

        msg = f"{SERVER_STATUS_ICONS.get(status.online_status, '⁉️')} {status.online_status.name} - version {status.version}\n"
        if status.time:
            msg += f"**In game time**: {status.time}\n"
        if status.stop_join_in:
            msg += f"**Stop join in**: {status.stop_join_in}\n"

        msg += f"\n{len(status.players)} connected player(s){':' if len(status.players) > 0 else ''}\n"
        for player in status.players:
            msg += f"\n- {player}"

        await interaction.response.send_message(msg, ephemeral=True)

    except Exception as exc:
        await interaction.response.send_message(f"❌ error: {exc}", ephemeral=True)
