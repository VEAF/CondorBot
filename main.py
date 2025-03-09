import logging
from rich import print
from discord import Message, Intents, Member, Interaction, SelectOption
from discord.ext import commands
from discord import ui
from condor.flight_plan import list_flight_plans
from condor.server_manager import (
    OnlineStatus,
    attach_server,
    is_server_running,
    refresh_server_status,
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


@bot.group()
async def condor(ctx):
    if ctx.invoked_subcommand is None:
        msg = """
**Condor 3 bot help**
        
Commands: /condor <command>
        
    start   start Condor 3 server
    stop    stop Condor 3 server
    list    list flight plans
    show    show informations about a flightplan
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
    status = refresh_server_status()
    if status.online_status != OnlineStatus.OFFLINE.value:
        await ctx.send("❌ server is already running, server should be stopped first")
        return
    try:
        view = SelectFlightPlanView(ctx.author)
        await ctx.send("📋 Select a flight plan:", view=view)

        await view.wait()  # wait for user answer
        if view.response:
            flight_plan = view.response
            await ctx.send(f"📋 Selected flight plan: **{flight_plan}**\n*starting server*")
            start_server(flight_plan)
            await ctx.send(f"✅ server started with flight plan {flight_plan}")
        else:
            await ctx.send("⏳ elapsed time, operation cancelled.")

    except Exception as exc:
        await ctx.send(f"❌ an error occured, server not started: {exc}")
        return


@condor.command(description="Refresh condor 3 server status")
async def status(ctx):
    await on_status(ctx)


@condor.command(description="Stop condor 3 server")
async def stop(ctx):
    try:
        status = refresh_server_status()
        if status.online_status == OnlineStatus.OFFLINE.value:
            await ctx.send("❌ server is not running, so it couldn't be stopped")
            return
        if status.online_status == OnlineStatus.RUNNING.value or len(status.players) == 0:
            stop_server()
            await ctx.send("✅ server stopped")
        else:
            await ctx.send(f"❌ server couldn't be stopped, {len(status.players)} player(s) are connected")
            return
    except Exception as exc:
        await ctx.send(f"❌ an error occured, server not stopped: {exc}")
        return


@condor.command(name="list", description="List flight plans available")
async def _list(ctx):
    await on_list_flight_plans(ctx)


@condor.command(description="Show informations about a flightplan")
async def show(ctx):
    await ctx.send("👨‍💻 developpment in progress")


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
    print("Starting Condor 3 Discord Bot")
    try:
        config = get_config()
        check_config(config)

        if not (process := is_server_running()):
            print("server is not already running")
        else:
            print(f"server is already [yellow]running[/yellow] pid={process}, connecting to the app")
            attach_server()

    except Exception as e:
        print(f"[red]error loading configuration[/red]: {e}")
        return

    print(f"[yellow]admin channel[/yellow]: [blue]{config.discord.admin_channel_id}[/blue]")
    bot.run(config.discord.api_token)


if __name__ == "__main__":
    main()
