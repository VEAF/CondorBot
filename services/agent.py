import os
from discord import Message, Attachment
from condor.config import get_config
from condor.flight_plan import FlightPlan, list_flight_plans, load_flight_plan
from condor.server_manager import refresh_server_status, OnlineStatus

SERVER_STATUS_ICONS = {
    OnlineStatus.OFFLINE: "❌",
    OnlineStatus.RUNNING: "💿",
    OnlineStatus.JOINING_ENABLED: "🕑",
    OnlineStatus.JOINING_DISABLED: "✈️",
}


async def on_flight_plan_upload(message: Message, attachment: Attachment) -> None:
    file_name = attachment.filename

    print(f"a new flight plan was received: {file_name}")

    local_filepath = f"{get_config().flight_plans_path}/{file_name}"
    await attachment.save(local_filepath)

    try:
        flight_plan = load_flight_plan(local_filepath)

        msg = f"✅ {message.author} has uploaded a new flight plan:\n\n"
        msg += f"**Flight Plan**: {flight_plan.filename}\n"
        msg += f"**Length**: {flight_plan.distance / 1000:.0f} km\n"
        msg += f"**Turn points**: {len(flight_plan.turnpoints)}\n"
        for tp in flight_plan.turnpoints:
            msg += f"- {tp.name}\n"

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


async def on_list_flight_plans(ctx) -> None:
    fpl = list_flight_plans()
    msg = f"{'✅' if len(fpl) > 0 else '❌'} {len(fpl)} flight plans available:\n\n"
    for fp in fpl:
        msg += f"- {fp.filename.split('\\')[-1]} *{fp.landscape} - {fp.distance / 1000:.0f} km*\n"

    await ctx.channel.send(msg)


async def on_status(ctx) -> None:
    try:
        status = refresh_server_status()

        msg = SERVER_STATUS_ICONS.get(status.online_status, "⁉️") + " " + str(status.online_status.name) + "\n"
        if status.time:
            msg += f"**In game time**: {status.time}\n"
        if status.stop_join_in:
            msg += f"**Stop join in**: {status.stop_join_in}\n"
        await ctx.channel.send(msg)

    except Exception as exc:
        await ctx.channel.send(f"❌ error: {exc}")
