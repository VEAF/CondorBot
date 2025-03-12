import logging
from rich import print
from discord import Interaction, Message, Intents
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
from services.dialogs import SelectFlightPlanView

intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

logger = logging.getLogger("main")


@bot.tree.command(description="Display the help")
async def condor(interaction: Interaction):
    msg = f"""
**Condor 3 bot help** - *v{release.version}*

```        
Commands: /condor <command>
        
    start   start Condor 3 server
    stop    stop Condor 3 server
    list    list flight plans
    show    show informations about a flightplan
    ping    test if the discord bot is alive

    help    show this help message
```

Upload: just send a new Flight Plan (ex: MyFlightPlan.fpl) to this channel.

"""

    await interaction.response.send_message(msg, ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ bot is logged in as {bot.user}")


@bot.tree.command(description="Simple Ping Pong Test command")
async def ping(interaction: Interaction):
    await interaction.response.send_message("Pong! 🏓", ephemeral=True)


@bot.tree.command(description="Start condor 3 server")
async def start(interaction: Interaction):
    status, _ = get_server_status()
    if status.online_status != OnlineStatus.OFFLINE.value:
        await interaction.response.send_message(
            "❌ server is already running, server should be stopped first", ephemeral=True
        )
        return
    try:
        view = SelectFlightPlanView(interaction.user)
        await interaction.response.send_message("📋 Select a flight plan:", view=view, ephemeral=True)

        await view.wait()
        if view.response:
            flight_plan = view.response
            channel = interaction.channel
            start_server(flight_plan)
            await channel.send(
                f"✅ server started with flight plan {flight_plan} by **{interaction.user.display_name}**"
            )
        else:
            await interaction.response.send_message("⏳ elapsed time, operation cancelled.", ephemeral=True)

    except Exception as exc:
        await interaction.response.send_message(f"❌ an error occured, server not started: {exc}", ephemeral=True)
        return


@bot.tree.command(name="status", description="Refresh condor 3 server status")
async def status(interaction: Interaction):
    await on_status(interaction)


@bot.tree.command(description="Stop condor 3 server")
async def stop(interaction: Interaction):
    try:
        status, _ = get_server_status()
        if status.online_status == OnlineStatus.OFFLINE.value:
            await interaction.response.send_message(
                "❌ server is not running, so it couldn't be stopped", ephemeral=True
            )
            return
        if status.online_status == OnlineStatus.NOT_RUNNING.value or len(status.players) == 0:
            channel = interaction.channel
            stop_server()
            await interaction.response.send_message("done", delete_after=1)
            await channel.send(f"🔴 server stopped by **{interaction.user.display_name}**")
        else:
            await interaction.response.send_message(
                f"❌ server couldn't be stopped, {len(status.players)} player(s) are connected", ephemeral=True
            )
            return
    except Exception as exc:
        print(f"[red]{exc}[/red]")
        await interaction.response.send_message(f"❌ an error occured, server not stopped: {exc}", ephemeral=True)
        return


@bot.tree.command(name="list", description="List flight plans available")
async def _list(interaction: Interaction):
    await on_list_flight_plans(interaction)


@bot.tree.command(description="Show informations about a flightplan")
async def show(interaction: Interaction):
    await interaction.response.send_message("👨‍💻 developpment in progress", ephemeral=True)


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
    bot.run(config.discord.api_token)


if __name__ == "__main__":
    main()
