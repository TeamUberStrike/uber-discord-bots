import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

MAP_POOL = [
    "**CuberStrike**",
    "**SuperPRISM Reactor**",
    "**Sky Garden**",
    "**Temple of the Raven**",
    "**Hangar**",
    "**The Warehouse**",
    "**Space City**",
    "**Fort Winter**",
    "**Aqualab Research Hub**",
]

veto_sessions = {}

class VetoSession:
    def __init__(self, thread, player1, player2):
        self.thread = thread
        self.players = [player1, player2]
        random.shuffle(self.players)
        self.current_turn = 0
        self.remaining_maps = MAP_POOL.copy()
        self.banned_maps = []
        self.completed = False

    def current_player(self):
        return self.players[self.current_turn]

    def next_turn(self):
        self.current_turn = 1 - self.current_turn


async def start_veto_in_thread(thread, player1, player2):
    thread_id = thread.id

    if thread_id in veto_sessions and veto_sessions[thread_id].completed:
        return

    session = VetoSession(thread, player1, player2)
    veto_sessions[thread_id] = session

    maps_list = "\n".join([f"{i+1}. {m}" for i, m in enumerate(session.remaining_maps)])

    await thread.send(f"🗺️ **Veto started! Maps:**\n{maps_list}")
    await thread.send(f"🎯 {session.current_player().mention} bans first. Use: `!ban <number>`")


async def fetch_thread_first_message(thread: discord.Thread):
    first_msg = None
    async for m in thread.history(limit=1, oldest_first=True):
        first_msg = m
        break
    return first_msg


@bot.command(name="veto")
async def veto(ctx, arg=None):
    if ctx.channel.name.lower() != "events-admin":
        return

    if arg != "start":
        await ctx.send("Use: `!veto start`")
        return

    scoring = discord.utils.find(lambda c: c.name.lower() == "scoring", ctx.guild.channels)
    if scoring is None:
        await ctx.send("❌ Could not find the 'scoring' forum.")
        return

    started = 0

    for thread in scoring.threads:
        if thread.archived:
            continue

        try:
            first_msg = await fetch_thread_first_message(thread)
        except Exception:
            await ctx.send(f"⚠️ Could not read messages in `{thread.name}`.")
            continue

        if not first_msg:
            await ctx.send(f"⚠️ Could not find the creation message in `{thread.name}`.")
            continue

        mentions = first_msg.mentions

        if len(mentions) < 2:
            await ctx.send(f"⚠️ Not enough player mentions in `{thread.name}`.")
            continue

        player1 = mentions[0]
        player2 = mentions[1]

        if not isinstance(player1, discord.Member) or not isinstance(player2, discord.Member):
            await ctx.send(f"⚠️ Mentions in `{thread.name}` are not valid members.")
            continue

        await start_veto_in_thread(thread, player1, player2)
        started += 1

    await ctx.send(f"✅ Initialized map picking in **{started} threads**.")


@bot.command(name="ban")
async def ban(ctx, *, map_index: str):
    thread_id = ctx.channel.id

    if thread_id not in veto_sessions:
        return

    session = veto_sessions[thread_id]

    if session.completed:
        return

    if ctx.author != session.current_player():
        return

    if not map_index.isdigit():
        return

    index = int(map_index) - 1
    if index < 0 or index >= len(session.remaining_maps):
        return

    map_to_ban = session.remaining_maps[index]
    session.remaining_maps.remove(map_to_ban)
    session.banned_maps.append(map_to_ban)

    await ctx.send(f"❌ {ctx.author.mention} banned **{map_to_ban}**")

    if len(session.remaining_maps) == 3:
        random.shuffle(session.remaining_maps)  # <-- SHUFFLE HERE
        final_maps = "\n".join([f"{i+1}. {m}" for i, m in enumerate(session.remaining_maps)])
        await ctx.send(f"🏁 **Veto complete! Final three maps (randomized), listed in playing order are:**\n{final_maps}")
        session.completed = True
        await notify_if_all_done()
        return

    session.next_turn()

    maps_list = "\n".join([f"{i+1}. {m}" for i, m in enumerate(session.remaining_maps)])
    await ctx.send(
        f"➡️ Next: {session.current_player().mention} bans.\n"
        f"Remaining maps:\n{maps_list}"
    )


async def notify_if_all_done():
    admin = discord.utils.find(lambda c: c.name.lower() == "admin", bot.get_all_channels())
    if not admin:
        return

    if all(s.completed for s in veto_sessions.values()) and len(veto_sessions) > 0:
        await admin.send("🎉 **All tournament players picked maps!**")


bot.run(TOKEN)
