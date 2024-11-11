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
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Game variables
campaigns = database.get_all()

# Common messages
NOT_DUNGEON_MASTER = lambda campaign_name : f"It looks like you aren't the dungeon master of `{campaign_name}`. Only the campaign's dungeon master can call this command."
NOT_PLAYER_NO_ACCESS = lambda campaign_name : f"It looks like you aren't a player in `{campaign_name}`. Only the campaign's players can call this command."
NOT_PLAYER_NO_REMOVE = lambda campaign_name, username : f"No user with the name `{username}` exists in `{campaign_name}`, so you can't remove them from the campaign."
NO_CAMPAIGN_FOUND = lambda campaign_name : f"No campaign was found with the name `{campaign_name}`! Use `/campaign show all` to get a list of all created campaigns."
ITEM_EXISTS = lambda campaign_name, item_name : f"There's already an item with the name `{item_name}` in `{campaign_name}`. Please try again with a different name."
MANAGE_MODE_NOT_ACTIVE = "Whoops! It looks like management mode hasn't been enabled for any campaigns. Activate it using `/campaign manage` followed by the name of your campaign to use this command."
PLAY_MODE_NOT_ACTIVE = "Whoops! It looks like play mode hasn't been enabled for any campaigns. Activate it using `/campaign play` followed by the name of your campaign to use this command."

# Campaign modes
class CampaignMode(Enum):
  MANAGE = "manage"
  PLAY = "play"
  NONE = "none"

mode = CampaignMode.NONE
campaign_index = -1

# Item types
class ItemType(Enum):
  RESOURCE = "Resource"
  MELEE_WEAPON = "Melee weapon"
  RANGE_WEAPON = "Range weapon"

# Game functions
def display_campaign_details(index):
  result = ""
  # The name of the campaign and its dungeon master
  result += f"{index + 1}. `{campaigns[index]['name']}`\n> Dungeon Master: `{campaigns[index]['dungeon_master']}`"
  # The players of the campaign
  if len(campaigns[index]["players"]) > 0:
    result += "\n> Players:"
    for j in range(len(campaigns[index]["players"])):
      result += f"\n> {j + 1}. `{campaigns[index]['players'][j]['name']}`"
  # If the campaign has no players
  else:
    result += "\n> This campaign has no players."
  # The items of the campaign
  if len(campaigns[index]["items"]) > 0:
    result += "\n> Items:"
    items = campaigns[index]["items"]
    items_keys = list(items.keys())
    for j in range(len(items_keys)):
      item_details = f"{items[items_keys[j]]['type']}"
      result += f"\n> {j + 1}. `{items_keys[j]}`: {item_details}"
  else:
    result += "\n> This campaign has no items."
  result += "\n"
  return result

# Check if a user is the dungeon master of a campaign
async def is_dungeon_master(campaign, interaction):
  if campaign["dungeon_master"] == interaction.user.name:
    return True
  await interaction.response.send_message(NOT_DUNGEON_MASTER(campaign["name"]))
  return False

# Check if a user is a player in a campaign
async def is_player(campaign, interaction, username, is_player_only_command):
  for i in range(len(campaign["players"])):
    if campaign["players"][i]["name"] == username:
      return campaign["players"][i]
  if is_player_only_command:
    await interaction.response.send_message(NOT_PLAYER_NO_ACCESS(campaign["name"]))
  else:
    await interaction.response.send_message(NOT_PLAYER_NO_REMOVE(campaign["name"], username))
  return None

async def does_item_exist(item_name, campaign, interaction):
  if item_name in list(campaign["items"].keys()):
    await interaction.response.send_message(ITEM_EXISTS(campaign["name"], item_name))
    return True
  return False

# Check if management mode is active
async def is_manage_mode(interaction):
  if mode == CampaignMode.MANAGE:
    return True
  await interaction.response.send_message(MANAGE_MODE_NOT_ACTIVE)
  return False

# Check if play mode is active
async def is_play_mode(interaction):
  if mode == CampaignMode.PLAY:
    return True
  await interaction.response.send_message(PLAY_MODE_NOT_ACTIVE)
  return False

# Change the type of commands that can be used
async def change_mode(new_mode, name, interaction):
  for i in range(len(campaigns)):
    # Find the campaign with the given name
    if campaigns[i]["name"] == name:
      # If the player owns the campaign, change the mode
      if await is_dungeon_master(campaigns[i], interaction):
        global mode, campaign_index
        mode = new_mode
        campaign_index = i
        if new_mode == CampaignMode.MANAGE:
          await interaction.response.send_message(f"You can now access management commands for `{campaigns[i]['name']}`.")
        elif new_mode == CampaignMode.PLAY:
          await interaction.response.send_message(f"You can now access play commands for `{campaigns[i]['name']}`.")
        elif new_mode == CampaignMode.NONE:
          await interaction.response.send_message(f"Exited `{campaigns[i]['name']}`.")
      break
  else:
    await interaction.response.send_message(NO_CAMPAIGN_FOUND(name))

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
@app_commands.describe(command="command", name="name")
async def campaign(interaction: discord.Interaction, command: str, name: str):
  match command:
    # Create a new campaign
    case "create":
      # If the campaign name is "all", it could can cause issues with other commands
      if name == "all":
        await interaction.response.send_message("The campaign name cannot be `all`.")
      for campaign in campaigns:
        if campaign["name"] == name:
          await interaction.response.send_message(f"Whoops, it looks like there's already another campaign with the name `{name}`! Please try again with a different name.")
          break
      else:
        new_campaign = {
          "name": name,
          "dungeon_master": interaction.user.name,
          "players": [],
          "items": {}
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
          await interaction.response.send_message(NO_CAMPAIGN_FOUND(name))
          return
      await interaction.response.send_message(result)
    # Enable management commands for a campaign
    case "manage":
      await change_mode(CampaignMode.MANAGE, name, interaction)
    # Enable play commands for a campaign
    case "play":
      await change_mode(CampaignMode.PLAY, name, interaction)
    # Disable management and play commands
    case "exit":
      await change_mode(CampaignMode.NONE, name, interaction)
    # If an unknown command has been given
    case _:
      await interaction.response.send_message("Whoops! Looks like you provided an invalid command. Use `/help` for more info.")

# Change the name of a campaign
@bot.tree.command(name="changename")
@app_commands.describe(name="name")
async def change_name(interaction: discord.Interaction, name: str):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction):
    campaigns[campaign_index]["name"] = name
    database.update_item(campaigns[campaign_index])
    await interaction.response.send_message(f"Changed the name of the campaign to `{name}`.")

# Add a player to a campaign
@bot.tree.command(name="addplayer")
@app_commands.describe(username="username")
async def add_player(interaction: discord.Interaction, username: str):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction):
    for member in interaction.guild.members:
      if member.name == username:
        for player in campaigns[campaign_index]["players"]:
          if player["name"] == username:
            await interaction.response.send_message(f"`{username}` is already a player in `{campaigns[campaign_index]['name']}`.")
            return
        campaigns[campaign_index]["players"].append({
          "name": username,
          "inventory": []
        })
        database.update_item(campaigns[campaign_index])
        await interaction.response.send_message(f"`{username}` is now a player in `{campaigns[campaign_index]['name']}`.")
        return
    await interaction.response.send_message(f"No user with the name `{username}` exists in this server.")

# Remove a player from a campaign
@bot.tree.command(name="removeplayer")
@app_commands.describe(username="username")
async def add_player(interaction: discord.Interaction, username: str):
  player = await is_player(campaigns[campaign_index], interaction, username, False)
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction) and player:
    campaigns[campaign_index]["players"].remove(player)
    database.update_item(campaigns[campaign_index])
    await interaction.response.send_message(f"`{username}` is no longer a player in `{campaigns[campaign_index]['name']}`.")

# Create a new item that can be used in the campaign
@bot.tree.command(name="addresource")
@app_commands.describe(name="name")
async def add_resource(interaction: discord.Interaction, name: str):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction) and not await does_item_exist(name, campaigns[campaign_index], interaction):
    campaigns[campaign_index]["items"].update({
      name: {
        "type": ItemType.RESOURCE.value
      }
    })
    database.update_item(campaigns[campaign_index])
    await interaction.response.send_message(f"A new resource with the name `{name}` has been added to `{campaigns[campaign_index]['name']}`.")

# Run the bot
bot.run(TOKEN)
