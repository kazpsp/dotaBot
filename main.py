import requests
import json
from typing import Literal, Optional
import discord
from discord.ext.commands import Greedy, Context
from discord import app_commands, Interaction
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)
guild = discord.Object(id='694345549931085924')

@bot.tree.command()
async def help(interaction: discord.Interaction):
    """Help""" #Description when viewing / commands
    await interaction.response.send_message("NO SEA SAPO VALE MIA, APRENDE A JUGAR MALPARIDO")

@bot.tree.command()
async def createguild(interaction: discord.Interaction, guild_name: str, guild_description: str):
    """Create Guild"""  # Description when viewing / commands
    credentials, token_url = load_credentials_from_json('env.json', 'sandbox', 'partial_copy')
    try:
        auth = get_salesforce_access_token(credentials)
    except Exception as e:
        print(str(e))

    instance_url = auth['instance_url'];
    url = f'{instance_url}/services/apexrest/guildAPI/'
    tok = auth['access_token']
    headers = {
        'Authorization': f'Bearer {tok}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': guild_name,
        'description': guild_description
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        guild_id = response.json()
        await interaction.response.send_message(f'Guild created with ID: {guild_id}')
    else:
        await interaction.response.send_message(f'Failed to create guild. Status Code: {response.status_code}, Error: {response.text}')

@bot.tree.command()
async def createplayer(interaction: discord.Interaction, player_name: str, player_notes: str):
    """Create Player"""  # Description when viewing / commands
    credentials, token_url = load_credentials_from_json('env.json', 'sandbox', 'partial_copy')
    try:
        auth = get_salesforce_access_token(credentials)
    except Exception as e:
        await interaction.response.send_message(f'Failed to authenticate to Salesforce: {str(e)}')
        return

    instance_url = auth['instance_url']
    url = f'{instance_url}/services/apexrest/playerAPI/'  # Assuming you have a REST API for Player__c
    tok = auth['access_token']
    headers = {
        'Authorization': f'Bearer {tok}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': player_name,
        'notes': player_notes
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        player_id = response.json()
        await interaction.response.send_message(f'Player created with ID: {player_id}')
    else:
        await interaction.response.send_message(f'Failed to create player. Status Code: {response.status_code}, Error: {response.text}')

@bot.tree.command()
async def getplayer(interaction: discord.Interaction, player_name: str):
    """Get Player"""  # Description when viewing / commands
    credentials, token_url = load_credentials_from_json('env.json', 'sandbox', 'partial_copy')
    try:
        auth = get_salesforce_access_token(credentials)
    except Exception as e:
        await interaction.response.send_message(f'Failed to authenticate to Salesforce: {str(e)}')
        return

    instance_url = auth['instance_url']
    url = f'{instance_url}/services/apexrest/playerAPI/?player_name={player_name}'  # Replace with your specific API endpoint
    tok = auth['access_token']
    headers = {
        'Authorization': f'Bearer {tok}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        player_data = response.json()
        player_name = player_data.get('Name', 'N/A')
        player_notes = player_data.get('Notes__c', 'N/A')
        await interaction.response.send_message(f"Player Name: {player_name}\nPlayer Notes: {player_notes}")
        await interaction.response.send_message("asd")
    else:
        await interaction.response.send_message("basd")


@bot.tree.command()
async def getguild(interaction: discord.Interaction, guild_name: str):
    """Get Guild Information"""  # Description when viewing / commands
    credentials, token_url = load_credentials_from_json('env.json', 'sandbox', 'partial_copy')

    try:
        auth = get_salesforce_access_token(credentials)
    except Exception as e:
        await interaction.response.send_message(f'Error authenticating: {str(e)}')
        return

    instance_url = auth['instance_url']
    url = f'{instance_url}/services/apexrest/guildAPI/?guild_name={guild_name}'  # Sending guild_name as a query parameter

    headers = {
        'Authorization': f'Bearer {auth["access_token"]}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.text:  # Check if the response body is not empty
        try:
            guild_data = response.json()
            # Format and send the data as you see fit. For now, I'm assuming the data has 'name' and 'description'.
            print(guild_data)
            await interaction.response.send_message(
                f'Guild Name: {guild_data["Name"]}\nDescription: {guild_data["Description__c"]}')
        except json.JSONDecodeError:
            await interaction.response.send_message(f'Error decoding JSON response: {response.text}')
    else:
        await interaction.response.send_message(
            f'No data returned from Salesforce. Status Code: {response.status_code}')


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

def load_credentials_from_json(json_file_path, environment, instance):
    with open(json_file_path, 'r') as f:
        config = json.load(f)

    credentials = config[environment][instance]['credentials']
    token_url = config[environment][instance]['token_url']

    return credentials, token_url

def get_salesforce_access_token(credentials):
    domain = credentials['domain']
    endpoint = f"https://{domain}.salesforce.com/services/oauth2/token"

    username = credentials['username'],
    password = credentials['password'],
    security_token = credentials['security_token'],
    client_id = credentials['client_id'],
    client_secret = credentials['client_secret'],

    password2 = password+security_token
    print(password2)
    print(endpoint)
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {client_secret}")

    params = {
        'grant_type': 'password',
        'client_id': client_id,  # Consumer Key
        'client_secret': client_secret,  # Consumer Secret
        'username': username,
        'password': password2,  # Concatenating password and security token
    }

    print(params)
    response = requests.post(endpoint, data=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to authenticate: {response.text}")

@app_commands.command(name="test",description="test2")
async def ping(ctx: Interaction, have_account:bool, login_email:str=None, login_mobile:str=None):
    print('test')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    print(f'An error occurred: {error}')

@bot.command()
async def createGuild(ctx, name: str, description: str):

    credentials, token_url = load_credentials_from_json('env.json', 'sandbox', 'partial_copy')
    try:
        auth = get_salesforce_access_token(credentials)
    except Exception as e:
        print(str(e))

    instance_url = auth['instance_url'];
    url = f'{instance_url}/services/apexrest/guildAPI/'
    tok = auth['access_token']
    headers = {
        'Authorization': f'Bearer {tok}',
        'Content-Type': 'application/json'
    }
    data = {
        'name': name,
        'description': description
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200 or response.status_code == 201:
        guild_id = response.json()
        await ctx.send(f'Guild created with ID: {guild_id}')
    else:
        await ctx.send(f'Failed to create guild. Status Code: {response.status_code}, Error: {response.text}')


with open('env.json', 'r') as f:
    config = json.load(f)

discordToken = config['discord-bot']
bot.run(discordToken)
