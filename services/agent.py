import os
from discord import Message, Attachment
from condor.config import get_config
from condor.flight_plan import load_flight_plan


async def on_flight_plan_upload(message: Message, attachment: Attachment) -> None:
    file_name = attachment.filename

    print(f"a new flight plan was received: {file_name}")

    local_filepath = f"{get_config().flight_plans_path}/{file_name}"
    await attachment.save(local_filepath)

    try:
        flight_plan = load_flight_plan(local_filepath)

        msg = f"✅ {message.author} has uploaded a new flight plan:\n"
        msg += "\n"
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
