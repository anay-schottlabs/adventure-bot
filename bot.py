import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os
import database
from enum import Enum

# Getting the bot token
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Create the bot object
bot = commands.Bot(command_prefix = "!", intents = discord.Intents.default())

# Game variables
campaigns = database.get_all()

# Campagin modes
class CampaignMode(Enum):
  MANAGE = 1
  PLAY = 2
  NONE = 3

mode = CampaignMode.NONE
campaign_index = -1

# Game functions
def display_campaign_details(index):
  result = ""
  # The name of the campaign and its dungeon master
  result += f"{index + 1}. `{campaigns[index]['name']}`\n> Dungeon Master: `{campaigns[index]['dungeon_master']}`"
  # The players of the campaign
  if len(campaigns[index]["players"]) > 0:
    result += f"\n> Players:"
    for j in range(len(campaigns[index]["players"])):
      result += f"\n> {j + 1}. {campaigns[index]['players'][j]['name']}"
  # If the campaign has no players
  else:
    result += f"\n> This campaign has no players."
  result += "\n"
  return result

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
      for campaign in campaigns:
        if campaign["name"] == name:
          await interaction.response.send_message(f"Whoops, it looks like there's already another campaign with the name `{name}`! Please try again with a different name.")
          break
      else:
        new_campaign = {
          "name": name,
          "dungeon_master": interaction.user.name,
          "players": [],
          "items": []
        }
        campaigns.append(database.add_item(new_campaign))
        await interaction.response.send_message(f"A new campaign with the name `{name}` has been created.")
    # See the details of campaigns
    case "show":
      if len(campaigns) == 0:
        await interaction.response.send_message("No campaigns have been created yet! Use `/campaign create` to create a new one!")
        return
      result = ""
      for i in range(len(campaigns)):
        # If we are showing all campaigns, add this campaign's details to the list
        if name == "all":
          result += display_campaign_details(i)
        # If we are showing a specific campaign, set the list's value to its details
        elif campaigns[i]["name"] == name:
          result = display_campaign_details(i)
          break
      else:
        if name != "all":
          await interaction.response.send_message(f"No campaign was found with the name `{name}`! Use `/campaign show all` to get a list of all created campaigns.")
          return
      await interaction.response.send_message(result)
    # Enable management commands for a campaign
    case "manage":
      for campaign in campaigns:
        if campaign["name"] == name:
          global selected_campaign
          selected_campaign = campaign
          break
      else:
        await interaction.response.send_message(f"No campaign was found with the name `{name}`! Use `/campaign show all` to get a list of all created campaigns.")
        return
      if selected_campaign["dungeon_master"] != interaction.user.name:
        await interaction.response.send_message(f"It looks like you aren't the dungeon master of `{campaign['name']}`! Only the campaign's dungeon master can call this command.")
        return
      else:
        mode = CampaignMode.MANAGE
        campaign_index = campaigns.index(selected_campaign)
        await interaction.response.send_message(f"You can now access management commands for `{campaigns[campaign_index]['name']}`.")
    # Enable play commands for a campaign
    case "play":
      for campaign in campaigns:
        if campaign["name"] == name:
          selected_campaign = campaign
          break
      else:
        await interaction.response.send_message(f"No campaign was found with the name `{name}`! Use `/campaign show all` to get a list of all created campaigns.")
        return
      if selected_campaign["dungeon_master"] != interaction.user.name:
        await interaction.response.send_message(f"It looks like you aren't the dungeon master of `{campaign['name']}`! Only the campaign's dungeon master can call this command.")
        return
    # If an unknown command has been given
    case _:
      await interaction.response.send_message("Whoops! Looks like you provided an invalid command. Use `/help` for more info.")

# Run the bot
bot.run(TOKEN)
