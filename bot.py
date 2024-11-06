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
campaigns = database.get_all()

# Formatting variables
INDENT_SPACES = 8

@bot.event
async def on_ready():
  try:
    # Sync the bot's commands
    synced_commands = await bot.tree.sync()
    print(f"Successfully synced {len(synced_commands)} command/s.")
  except Exception as e:
    print(e)

# Commands associated with managing the campaigns
@bot.tree.command(name="campaign")
@app_commands.describe(command = "command", name = "name")
async def campaign(interaction: discord.Interaction, command: str, name: str):
  match command:
    # Create a new campaign
    case "create":
      # If the campaign name is "all", it could can cause issues with other commands
      if name == "all":
        await interaction.response.send_message("The campaign name cannot be \"all\".")
      else:
        new_campaign = {
          "name": name,
          "dungeon_master": interaction.user.name,
          "players": [],
          "items": []
        }
        campaigns.append(database.add_item(new_campaign))
        await interaction.response.send_message(f"A new campaign with the name \"{name}\" has been created.")
    case "show":
      result = ""
      # Show the details of all campaigns
      if name == "all":
        for i in range(len(campaigns)):
          result += f"{i + 1}. {campaigns[i]['name']}\n{' ' * INDENT_SPACES}Dungeon Master: {campaigns[i]['dungeon_master']}\n"
          if len(campaigns[i]["players"]) > 0:
            result += f"{' ' * INDENT_SPACES}Players:\n"
            for j in range(len(campaigns[i]["players"])):
              result += f"{' ' * ((INDENT_SPACES * 2) - (INDENT_SPACES))}{j + 1}. {campaigns[i]['players'][j]['name']}\n"
          else:
            result += f"{' ' * INDENT_SPACES}This campaign has no players."
      # Show the details of a specific campaign
      else:
        pass
      await interaction.response.send_message(result)
    # If an unknown command has been given
    case _:
      await interaction.response.send_message("Whoops! Looks like you provided an invalid command. Use /help for more info.")

# Run the bot
bot.run(TOKEN)
