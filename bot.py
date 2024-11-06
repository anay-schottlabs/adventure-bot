import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import database

# Getting the bot token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Create the bot object
bot = commands.Bot(command_prefix = "!", intents = discord.Intents.default())

# Game variables
campaigns = []

@bot.event
async def on_ready():
  try:
    # Sync the bot's commands
    synced_commands = await bot.tree.sync()
    print(f"Successfully synced {len(synced_commands)} command/s.")
    # Load previous campaigns
    campaigns = database.get_all()
  except Exception as e:
    print(e)

@bot.tree.command(name="campaign") # Commands associated with managing the campaigns
@app_commands.describe(command = "command", name = "name")
async def campaign(interaction: discord.Interaction, command: str, name: str):
  match command:
    case "create":
      new_campaign = {
        "name": name,
        "dungeon_master": interaction.user.name,
        "players": [],
        "items": []
      }
      campaigns.append(database.add_item(new_campaign))
      await interaction.response.send_message(f"A new campaign with the name \"{name}\" has been created.")
    case _:
      await interaction.response.send_message("Whoops! Looks like you provided an invalid command. Use /help for more info.")


# Run the bot
bot.run(TOKEN)
