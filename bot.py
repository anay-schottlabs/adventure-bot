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
ITEM_CREATION = lambda campaign_name, item_name, item_type : f"A new {item_type} with the name `{item_name}` has been added to `{campaign_name}`."
INVALID_ROLL = lambda roll : f"Whoops! `{roll}` isn't a valid roll. Please enter a valid one instead."
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

# All possible dice that can be rolled
DICE = [ 4, 6, 8, 10, 12, 20, 100 ]

# Game functions
def display_campaign_details(index, show_num):
  result = ""
  # The name of the campaign and its dungeon master
  result += f"{index + 1 if show_num else 1}. `{campaigns[index]['name']}`\n> Dungeon Master: `{campaigns[index]['dungeon_master']}`"
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
      item = items[items_keys[j]]
      item_details = f"{item['type']}"
      if item['type'] != ItemType.RESOURCE.value:
        item_details += f", `{item['damage']}` damage"
        if item['type'] == ItemType.RANGE_WEAPON.value:
          item_details += f", `{item['range']}` feet range, `{item['projectile']}` as projectile"
      result += f"\n> {j + 1}. `{items_keys[j]}`: {item_details}"
  # If the campaign has no items
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

# Check if an item's name has already been taken
async def does_item_exist(item_name, campaign, interaction, send_message):
  if item_name in list(campaign["items"].keys()):
    if send_message:
      await interaction.response.send_message(ITEM_EXISTS(campaign["name"], item_name))
    return True
  return False

# Check if a roll is valid
async def is_roll_valid(roll, interaction, with_addition):
  valid = True
  try:
    dice_amount = int(roll.split("d")[0])
    if dice_amount < 1:
      raise Exception
  except:
    valid = False
  try:
    if "+" in roll and with_addition:
      dice_type = int(roll.split("d")[1].split("+")[0])
      int(roll.split("d")[1].split("+")[1])
    elif "+" in roll and not with_addition:
      raise Exception
    else:
      dice_type = int(roll.split("d")[1])
    if dice_type not in DICE:
      raise Exception
  except:
    valid = False
  if not valid:
    await interaction.response.send_message(INVALID_ROLL(roll))
  return valid

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
          result += display_campaign_details(i, True)
        # If we are showing a specific campaign, set the list's value to its details
        elif campaigns[i]["name"] == name:
          result = display_campaign_details(i, False)
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
    await interaction.response.send_message(ITEM_CREATION(campaigns[campaign_index]["name"], name, "resource"))

# Create a new melee weapon that can be used in the campaign
@bot.tree.command(name="addmeleeweapon")
@app_commands.describe(name="name", damage_roll="damage_roll")
async def add_melee_weapon(interaction: discord.Interaction, name: str, damage_roll: str):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction) and not await does_item_exist(name, campaigns[campaign_index], interaction) and await is_roll_valid(damage_roll, interaction, False):
    campaigns[campaign_index]["items"].update({
      name: {
        "type": ItemType.MELEE_WEAPON.value,
        "hit": "1d20",
        "damage": damage_roll
      }
    })
    database.update_item(campaigns[campaign_index])
    await interaction.response.send_message(ITEM_CREATION(campaigns[campaign_index]["name"], name, "melee weapon"))

# Create a new ranged weapon that can be used in the campaign
@bot.tree.command(name="addrangeweapon")
@app_commands.describe(name="name", damage_roll="damage_roll", projectile="projectile", range_distance="range_distance")
async def add_range_weapon(interaction: discord.Interaction, name: str, damage_roll: str, projectile: str, range_distance: int):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction) and not await does_item_exist(name, campaigns[campaign_index], interaction, True) and await is_roll_valid(damage_roll, interaction, False):
    # Check if the item being used as the projectile has already been created in the campaign
    if not await does_item_exist(projectile, campaigns[campaign_index], interaction, False):
      await interaction.response.send_message(f"No item with the name {projectile} is currently part of this campaign, so you can't use it as this weapon's projectile. Use `/campaign show {campaigns[campaign_index]['name']}` to see the items in this campaign.")
    # The range of the weapon must be greater than zero and a multiple of 5
    elif range_distance % 5 != 0 and range_distance <= 0:
      await interaction.response.send_message(f"{range_distance} is not a valid range. Please ensure that the range of the weapon is greater than zero and a multiple of five.")
    else:
      campaigns[campaign_index]["items"].update({
        name: {
          "type": ItemType.RANGE_WEAPON.value,
          "hit": "1d20",
          "damage": damage_roll,
          "projectile": projectile,
          "range": range_distance
        }
      })
      database.update_item(campaigns[campaign_index])
      await interaction.response.send_message(ITEM_CREATION(campaigns[campaign_index]["name"], name, "ranged weapon"))

# Delete the campaign
@bot.tree.command(name="deletecampaign")
@app_commands.describe()
async def delete_campaign(interaction: discord.Interaction):
  if await is_manage_mode(interaction) and await is_dungeon_master(campaigns[campaign_index], interaction):
    # Get the name for the message
    name = campaigns[campaign_index]["name"]
    # Remove it from the list of campaigns and the database
    database.remove_item(campaigns[campaign_index])
    campaigns.remove(campaigns[campaign_index])
    # Exit management mode
    global mode
    mode = CampaignMode.NONE
    # Send the message with the name from earlier
    await interaction.response.send_message(f"The campaign `{name}` has been deleted.")

# Run the bot
bot.run(TOKEN)
