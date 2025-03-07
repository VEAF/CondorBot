import logging
import os
from rich import print
from discord import Attachment, Message, Intents
from discord.ext import commands
from condor import load_flight_plan
from config import check_config, get_config

intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

logger = logging.getLogger("main")


@bot.group()
async def condor(ctx):
    if ctx.invoked_subcommand is None:
        msg = """
**Condor 3 bot help**
        
Commands: /condor <command>
        
    start   start Condor 3 server
    stop    stop Condor 3 server
    ping    test if the discord bot is alive

Upload: just send a new Flight Plan (ex: MyFlightPlan.fpl) to this channel.

"""

        await ctx.send(msg)


@bot.event
async def on_ready():
    print(f"✅ bot is logged in as {bot.user}")


@condor.command(description="Simple Ping Pong Test command")
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@condor.command(description="Start condor 3 server")
async def start(ctx):
    await ctx.send("👨‍💻 developpment in progress")


@condor.command(description="Stop condor 3 server")
async def stop(ctx):
    await ctx.send("👨‍💻 developpment in progress")


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


@bot.event
async def on_message(message: Message):
    config = get_config()

    if message.author == bot.user or message.channel.id != config.discord.channel_id:
        return

    print(f"[yellow]message {message.author}[/yellow]@[blue]{message.channel.name}[/blue]: {message.content}")

    if message.attachments:
        await on_files_upload(message)

    await bot.process_commands(message)


def main():
    print("Starting Condor 3 Discord Bot")
    try:
        config = get_config()
        check_config(config)
    except Exception as e:
        print(f"[red]error loading configuration[/red]: {e}")
        return

    print(f"[yellow]files channel[/yellow]: [blue]{config.discord.channel_id}[/blue]")
    bot.run(config.discord.api_token)


if __name__ == "__main__":
    main()
