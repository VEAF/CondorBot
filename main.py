import logging
from rich import print
from discord import Message, Intents
from discord.ext import commands
from condor.server_manager import attach_server, is_server_running, start_server, stop_server
from condor.config import check_config, get_config
from services.agent import on_files_upload, on_list_flight_plans

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
async def start(ctx, flight_plan: str):
    if process := is_server_running():
        await ctx.send(f"❌ server is already running (pid: {process}), could not use start procedure")
        return
    try:
        start_server(flight_plan)
        await ctx.send(f"✅ server started with flight plan {flight_plan}")
    except Exception as exc:
        await ctx.send(f"❌ an error occured, server not started: {exc}")
        return


@condor.command(description="Refresh condor 3 server status")
async def status(ctx):
    await ctx.send("👨‍💻 developpment in progress")


@condor.command(description="Stop condor 3 server")
async def stop(ctx):
    if not is_server_running():
        await ctx.send("❌ server is not running, could not stop the server")
        return
    try:
        stop_server()
        await ctx.send("✅ server stopped")
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

    if message.author == bot.user or message.channel.id != config.discord.channel_id:
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

    print(f"[yellow]files channel[/yellow]: [blue]{config.discord.channel_id}[/blue]")
    bot.run(config.discord.api_token)


if __name__ == "__main__":
    main()
