import os
import random
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import feedparser
from openai import OpenAI

# ================= CONFIG =================
BOT_TOKEN = os.getenv("")
OPENAI_API_KEY = os.getenv("e03c1d36-4fbb-4c72-afc5-20357aab7610")

# Tenor key (hardcoded as requested)
TENOR_API_KEY = "AIzaSyBmDZbMeXyUvB37MvYCP1Lfe5M4-h8x-p0"

MAIN_CHANNEL_ID = "UCJj3O6UauXHDbU1aIkDx1zg"
SECOND_CHANNEL_ID = "UCyvheKFDbzSEtCkGwbYRSjw"

client = OpenAI(api_key=e03c1d36-4fbb-4c72-afc5-20357aab7610)

# ================= DISCORD =================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    activity=discord.Game(name="being kind 💖")
)

# ================= STATE =================
memory_enabled = {}
user_moods = {}
server_personality = {}
roleplay_mode = {}

# ================= MOOD DETECTION =================
HAPPY = ["happy", "great", "awesome", "love", "excited"]
SAD = ["sad", "down", "lonely", "cry"]
ANGRY = ["angry", "mad", "annoyed"]
STRESSED = ["stressed", "tired", "overwhelmed"]

def detect_mood(text):
    t = text.lower()
    if any(w in t for w in HAPPY): return "happy"
    if any(w in t for w in SAD): return "sad"
    if any(w in t for w in ANGRY): return "angry"
    if any(w in t for w in STRESSED): return "stressed"
    return "neutral"

# ================= PERSONALITIES =================
PERSONALITIES = {
    "default": "friendly, natural, supportive",
    "fun": "playful, humorous, upbeat",
    "calm": "gentle, soothing, reassuring",
    "hype": "energetic, excited, encouraging"
}

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Higlly’s bot is online as {bot.user}")

# ================= ADMIN CHECK =================
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# ================= /TALK =================
@bot.tree.command(name="talk", description="Talk to Higlly’s bot")
async def talk(interaction: discord.Interaction, message: str):
    guild = interaction.guild_id
    mood = detect_mood(message)

    if memory_enabled.get(guild, False):
        user_moods[(guild, interaction.user.id)] = mood

    personality = server_personality.get(guild, "default")
    roleplay = roleplay_mode.get(guild)

    system_prompt = (
        f"You are Higlly’s bot, a friendly character. "
        f"Personality: {PERSONALITIES[personality]}. "
        "Never say you are an AI, bot, or model. "
        "Never mention OpenAI."
    )

    if roleplay:
        system_prompt += f" You are roleplaying as: {roleplay}."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        max_tokens=150
    )

    await interaction.response.send_message(
        response.choices[0].message.content
    )

# ================= /PERSONALITY =================
@bot.tree.command(name="personality", description="Change Higlly’s bot personality")
async def personality(interaction: discord.Interaction, mode: str):
    if mode not in PERSONALITIES:
        await interaction.response.send_message("Modes: default, fun, calm, hype")
        return

    server_personality[interaction.guild_id] = mode
    await interaction.response.send_message(f"✨ Personality set to **{mode}**")

# ================= /ROLEPLAY =================
@bot.tree.command(name="roleplay", description="Start or stop roleplay")
async def roleplay(interaction: discord.Interaction, action: str, scenario: str = None):
    if action == "start" and scenario:
        roleplay_mode[interaction.guild_id] = scenario
        await interaction.response.send_message(f"🎭 Roleplay started: **{scenario}**")
    elif action == "stop":
        roleplay_mode.pop(interaction.guild_id, None)
        await interaction.response.send_message("🎬 Roleplay stopped.")
    else:
        await interaction.response.send_message(
            "Use: /roleplay start <scenario> or /roleplay stop"
        )

# ================= /IMAGE =================
@bot.tree.command(name="image", description="Generate an image")
async def image(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()

    response = client.images.generate(
        model="gpt-4o-mini",
        prompt=prompt,
        size="1024x1024"
    )

    embed = discord.Embed(title="🖼 Image by Higlly’s bot")
    embed.set_image(url=response.data[0].url)
    await interaction.followup.send(embed=embed)

# ================= /GIF =================
@bot.tree.command(name="gif", description="Find a GIF")
async def gif(interaction: discord.Interaction, query: str = "fun"):
    url = f"https://tenor.googleapis.com/v2/search?q={query}&key=AIzaSyBmDZbMeXyUvB37MvYCP1Lfe5M4&limit=10"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()

    await interaction.response.send_message(
        random.choice(data["results"])["media_formats"]["gif"]["url"]
    )

# ================= /LATESTVIDEOS =================
@bot.tree.command(name="latestvideos", description="Latest Higlly videos")
async def latestvideos(interaction: discord.Interaction):
    msgs = []
    for label, cid in [
        ("📺 Main Channel",  UCJj3O6UauXHDbU1aIkDx1zg),
        ("📹 Second Channel", UCyvheKFDbzSEtCkGwbYRSjw)
    ]:
        feed = feedparser.parse(
            f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        )
        if feed.entries:
            msgs.append(
                f"{label}\n{feed.entries[0].title}\n{feed.entries[0].link}"
            )
    await interaction.response.send_message("\n\n".join(msgs))

# ================= /CREDITS =================
@bot.tree.command(name="credits", description="Bot credits")
async def credits(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✨ Higlly’s bot Credits",
        description=(
            "Created for the **Higlly community** 💖\n"
            "Personality • Roleplay • Images • GIFs\n"
            "Built with Python & Discord"
        ),
        color=0xff69b4
    )
    await interaction.response.send_message(embed=embed)

# ================= ADMIN COMMANDS =================
@bot.tree.command(name="admin_memory", description="(Admin) Toggle memory")
async def admin_memory(interaction: discord.Interaction, state: str):
    if not is_admin(interaction):
        await interaction.response.send_message("🚫 Admin only.", ephemeral=True)
        return
    memory_enabled[interaction.guild_id] = (state.lower() == "on")
    await interaction.response.send_message(f"🧠 Memory set to **{state.upper()}**")

# ================= PING REPLIES =================
PING_REPLIES = [
    "Hey! 👋 What’s up?",
    "You called? 👀",
    "I’m here 😄 Try `/talk`",
    "Need something? ✨",
    "Hi there! 💖"
]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        await message.channel.send(random.choice(PING_REPLIES))

    await bot.process_commands(message)

# ================= RUN =================
bot.run()
