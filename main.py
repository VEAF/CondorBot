import logging
from rich import print
from discord import Interaction, InteractionResponded, Message, Intents
from discord.ext import commands
from condor import release
from condor.server_manager import (
    OnlineStatus,
    get_server_status,
    start_server,
    stop_server,
)
from condor.config import check_config, get_config
from services.agent import on_files_upload, on_list_flight_plans, on_status
from services.dialogs import (
    SelectStartFlightPlan,
    SelectViewFlightPlan,
    handle_error,
    send_response,
)

intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

logger = logging.getLogger("main")

prefix = get_config().command_prefix


@bot.tree.command(name=f"{prefix}help", description="Display the help")
async def condor(interaction: Interaction):
    # cmd_prefix
    msg = f"""
**Condor 3 bot help** - *v{release.version}*

```        
Commands:

"""
    for command in bot.tree.get_commands():
        msg += f"{command.name:10s} {command.description}\n"

    msg += """
```
Upload: just send a new Flight Plan (ex: MyFlightPlan.fpl) to this channel.

"""

    await send_response(interaction, msg)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ bot is logged in as {bot.user}")


@bot.tree.command(name=f"{prefix}ping", description="Simple Ping Pong Test command")
async def ping(interaction: Interaction):
    await send_response(interaction, "Pong! 🏓")


@bot.tree.command(name=f"{prefix}start", description="Start condor 3 server")
async def start(interaction: Interaction):
    status, _ = get_server_status()
    if status.online_status != OnlineStatus.OFFLINE.value:
        await handle_error(interaction, "server is already running, server should be stopped first")
        return
    try:
        view = SelectStartFlightPlan(interaction.user)
        await send_response(interaction, "📋 Select a flight plan:", view=view)

        await view.wait()
        if view.response:
            flight_plan = view.response
            start_server(flight_plan)
            await send_response(
                interaction,
                f"✅ server started with flight plan {flight_plan} by **{interaction.user.display_name}**",
                channel_message=True,
            )
            await interaction.delete_original_response()
        else:
            await send_response(interaction, "⏳ elapsed time, operation cancelled.")

    except InteractionResponded as already_responded:
        print(f"[red]{already_responded}[/red]")

    except Exception as exc:
        print(f"[red]{exc}[/red]")
        await handle_error(interaction, f"an error occured, server not started: {exc}")


@bot.tree.command(name=f"{prefix}status", description="Refresh condor 3 server status")
async def status(interaction: Interaction):
    await on_status(interaction)


@bot.tree.command(name=f"{prefix}stop", description="Stop condor 3 server")
async def stop(interaction: Interaction):
    try:
        status, _ = get_server_status()
        if status.online_status == OnlineStatus.OFFLINE.value:
            await handle_error(interaction, "server is not running, so it couldn't be stopped")
            return
        if status.online_status == OnlineStatus.NOT_RUNNING.value or len(status.players) == 0:
            await send_response(interaction, "stopping", delete_after=1)
            stop_server()
            await send_response(
                interaction, f"🔴 server stopped by **{interaction.user.display_name}**", channel_message=True
            )
        else:
            await handle_error(
                interaction, f"server couldn't be stopped, {len(status.players)} player(s) are connected"
            )

    except InteractionResponded as already_responded:
        print(f"[red]{already_responded}[/red]")

    except Exception as exc:
        print(f"[red]{exc}[/red]")
        await handle_error(interaction, f"an error occured, server not stopped: {exc}")


@bot.tree.command(name=f"{prefix}list", description="List flight plans available")
async def _list(interaction: Interaction):
    await on_list_flight_plans(interaction)


@bot.tree.command(name=f"{prefix}show", description="Show informations about a flightplan")
async def show(interaction: Interaction):
    try:
        view = SelectViewFlightPlan(interaction.user)
        await send_response(interaction, "📋 Select a flight plan:", view=view)
        await view.wait()
        if not view.response:
            await send_response(interaction, "⏳ elapsed time, operation cancelled.")

    except InteractionResponded as already_responded:
        print(f"[red]{already_responded}[/red]")

    except Exception as exc:
        print(f"[red]{exc}[/red]")
        await handle_error(interaction, f"an error occured, server not started: {exc}")


@bot.event
async def on_message(message: Message):
    config = get_config()

    if message.author == bot.user or message.channel.id != config.discord.admin_channel_id:
        return

    print(f"[yellow]message {message.author}[/yellow]@[blue]{message.channel.name}[/blue]: {message.content}")

    if message.attachments:
        await on_files_upload(message)

    await bot.process_commands(message)  # hack to propagate message to commands


def main():
    print(f"Starting Condor 3 Discord Bot - v{release.version}")
    try:
        config = get_config()
        check_config(config)

    except Exception as e:
        print(f"[red]error loading configuration[/red]: {e}")
        return

    print(f"[yellow]admin channel[/yellow]: [blue]{config.discord.admin_channel_id}[/blue]")
    print(f"[yellow]command prefix[/yellow]: [blue]{config.command_prefix}[/blue]")
    print("[yellow]registered commands[/yellow]:")
    for command in bot.tree.get_commands():
        print(f"  - [blue]{command.name}[/blue]  {command.description}")

    bot.run(config.discord.api_token)


if __name__ == "__main__":
    main()
