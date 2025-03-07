import os
import logging
from rich import print
from discord import Message, Client, Intents
from condor import load_flight_plan
from config import check_config, get_config, load_config

intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = Client(intents=intents)

logger = logging.getLogger("main")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: Message):
    config = get_config()
    print(f"[yellow]message {message.author}[/yellow]@[blue]{message.channel.name}[/blue]: {message.content}")

    if message.channel.id == config.discord.channel_id and message.attachments:
        for attachment in message.attachments:
            file_name = attachment.filename
            file_url = attachment.url

            extension = ".fpl"
            if file_name.endswith(extension):
                print(f"Flight plan received: {file_name} - {file_url}")
                local_filepath = f"{get_config().flight_plans_path}/{file_name}"
                await attachment.save(local_filepath)
                print(f"Saved {file_name}")

                flight_plan = load_flight_plan(local_filepath)
                print(f"flight_plan length: {flight_plan.distance / 1000:.0f} km")

                msg = f"{message.author} has uploaded a new flight plan:\n"
                msg += "\n"
                msg += f"**Flight Plan**: {flight_plan.filename}\n"
                msg += f"**Length**: {flight_plan.distance / 1000:.0f} km\n"
                msg += f"**Turn points**: {len(flight_plan.turnpoints)}\n"
                for tp in flight_plan.turnpoints:
                    msg += f"- {tp.name}\n"

                await message.channel.send(msg)


def main():
    print("Starting Condor 3 Discord Bot")
    try:
        config = get_config()
        check_config(config)
    except Exception as e:
        print(f"[red]error loading configuration[/red]: {e}")
        return

    print(f"[yellow]files channel[/yellow]: [blue]{config.discord.channel_id}[/blue]")
    client.run(config.discord.api_token)


if __name__ == "__main__":
    main()
