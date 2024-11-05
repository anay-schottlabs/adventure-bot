import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

# Getting the bot token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Create the bot object
bot = commands.Bot(command_prefix = "!", intents = discord.Intents.default())

# Sync the bot on startup
@bot.event
async def on_ready():
  try:
    synced_commands = await bot.tree.sync()
    print(f"Successfully synced {len(synced_commands)} command/s.")
  except Exception as e:
    print(e)

@bot.tree.command(name="speak")
@app_commands.describe(text = "text")
async def speak(interaction: discord.Interaction, text: str):
  await interaction.response.send_message(f"{interaction.user.name} says {text}")

# Run the bot
bot.run(TOKEN)
