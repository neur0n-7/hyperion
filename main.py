
#                                                                                              #
#                                                                                              #
#                                                                                              #
#       __  __     __  __     ______   ______     ______     __     ______     __   __         #
#      /\ \_\ \   /\ \_\ \   /\  == \ /\  ___\   /\  == \   /\ \   /\  __ \   /\ "-.\ \        #
#      \ \  __ \  \ \____ \  \ \  _-/ \ \  __\   \ \  __<   \ \ \  \ \ \/\ \  \ \ \-.  \       #
#       \ \_\ \_\  \/\_____\  \ \_\    \ \_____\  \ \_\ \_\  \ \_\  \ \_____\  \ \_\\"\_\      #
#        \/_/\/_/   \/_____/   \/_/     \/_____/   \/_/ /_/   \/_/   \/_____/   \/_/ \/_/      # 
#                                                                                              #
#                              Sarpedon Scoring Server Discord Bot                             #
#                    View leaderboard and team info directly in your server                    #
#                             https://github.com/neur0n-7/hyperion                             #
#                                                                                              #
#                                                                                              #
#                                                                                              #


import os
import requests
import json
import time

import discord
from discord import app_commands
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a
from bs4 import BeautifulSoup
from pprint import pprint

from keep_alive import keep_alive, start_self_ping

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

modgroup = app_commands.Group(name="mod", description="Commands accessible only to those with Manage Server permissions")

##############################################################################


def pull_leaderboard(interaction):
	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)

	url = server_urls[str(interaction.guild.id)]
	raw = requests.get(url).content
	soup = BeautifulSoup(raw, "html.parser")
	text = list(soup.find_all(string=True))
	cleaned = []
	for t in text:
		t = str(t)
		cleaned_t = t.replace("\n", "")
		cleaned_t = cleaned_t.replace(" ", "")
		if cleaned_t != "" and cleaned_t[0] != "\xa0":
			cleaned.append(cleaned_t)

	score_index = cleaned.index("Score")

	cleaned = cleaned[score_index + 1:]

	grouped = list(zip(*[cleaned[i::5] for i in range(5)]))
	grouped = [list(x) for x in grouped]

	output = t2a(
		header=["Position", "Name", "Images", "Time", "Total Score"],
		body=grouped,
		style=PresetStyle.ascii_borderless
	)

	splitted = output.split("\n")
	final = [x for x in splitted if "---" not in x]
	return final



def get_all_images(interaction):

	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	url = server_urls[str(interaction.guild.id)]

	raw = requests.get(url).content
	soup = BeautifulSoup(raw, "html.parser")
	text = list(soup.find_all(string=True))
	cleaned = []
	for t in text:
		t = str(t)
		cleaned_t = t.replace("\n", "")
		cleaned_t= cleaned_t.replace(" ","")
		if cleaned_t!="" and cleaned_t[0]!="\xa0":
			cleaned.append(cleaned_t)

	filter_index = cleaned.index("Filterbyimage:")
	rank_index = cleaned.index("Rank")

	return cleaned[filter_index+1:rank_index]


def image_leaderboard(image, interaction):
	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	url = server_urls[str(interaction.guild.id)]

	raw = requests.get(f"{url}image/{image}").content
	soup = BeautifulSoup(raw, "html.parser")
	text = list(soup.find_all(string=True))
	cleaned = []
	for t in text:
		t = str(t)
		cleaned_t = t.replace("\n", "")
		cleaned_t = cleaned_t.replace(" ", "")
		if cleaned_t != "" and cleaned_t[0] != "\xa0":
			cleaned.append(cleaned_t)

	score_index = cleaned.index("Score")
	cleaned = cleaned[score_index + 1:]

	grouped = list(zip(*[cleaned[i::4] for i in range(4)]))
	grouped = [list(x) for x in grouped]

	output = t2a(
		header=["Position", "Name", "Time", "Total Score"],
		body=grouped,
		style=PresetStyle.ascii_borderless
	)

	splitted = output.split("\n")
	final = [x for x in splitted if "---" not in x]
	return final


def check_no_redirect(url):
	try:
		response = requests.get(url, allow_redirects=True)
		if response.history:
			return response.status_code == response.url
		else:
			return True
	except requests.exceptions.RequestException as e:
		return False


def pull_team(team, interaction):
	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	url = server_urls[str(interaction.guild.id)]

	team = team.replace(" ", "").title()

	raw = requests.get(f"{url}team/{team}").content
	soup = BeautifulSoup(raw, "html.parser")
	text = list(soup.find_all(string=True))
	cleaned = []

	for t in text:
		cleaned_t = str(t).replace("\n", "")

		if cleaned_t.startswith("Scores Over Time"):
			break

		filler = (
			"html", "Σαρπηδών", "Announcements", "Login", "Leaderboard",
			"Team", "Play Time", "Total Score", "Elapsed", team, "Current Image",
			"Completion", "Found", "Penalties", "Points", "Last Update"
		)

		for f in filler:
			if f.lower() in cleaned_t.lower() or f.replace(" ", "") == "Image":
				break
		else:
			if cleaned_t.replace(" ", "") != "" and not cleaned_t.startswith("form"):
				cleaned.append(cleaned_t.strip().rstrip())

	overall = cleaned[:2]

	to_table = cleaned[3:]
	grouped = list(zip(*[to_table[i::8] for i in range(8)]))

	tables = {}

	for image in grouped:
		temp = list(image)
		image_name = temp.pop(0)

		headers = [
			"Play Time", "Elapsed Time", "Last Update", "Completion Time",
			"Found Vulns", "Penalties", "Points"
		]

		unformatted = []
		for header, value in zip(headers, temp):
			unformatted.append((header, value))

		tables[image_name] = t2a(
			body=unformatted,
			style=PresetStyle.thin
		)

	return overall, tables


def get_all_teams(interaction):
	return [j[1] for j in [i.split() for i in pull_leaderboard(interaction)[1:]]]


##############################################################################


@tree.command(name="ping", description="Checks if Hyperion is online")
async def ping_cmd(interaction: discord.Interaction):
	latency = round(interaction.client.latency * 1000)
	embedVar = discord.Embed(
		title=":white_check_mark:   Pong!",
		description=f"Hyperion is online.\nPing: {latency}ms",
		color=0x0d2d43
	)
	await interaction.response.send_message(embed=embedVar)


##############################################################################


@tree.command(name="help", description="List all Hyperion commands")
async def help_cmd(interaction: discord.Interaction):
	embedVar = discord.Embed(title="Help", color=0x0d2d43)
	embedVar.add_field(name="/help", value="List all Hyperion commands", inline=False)
	embedVar.add_field(name="/ping", value="Checks if Hyperion is online", inline=False)
	embedVar.add_field(name="/leaderboard", value="Fetches the current leaderboard- overall or for a specific image", inline=False)
	embedVar.add_field(name="/team", value="Fetches a team's information", inline=False)
	embedVar.add_field(name="/invite", value="Invite Hyperion to your own server", inline=False)
	embedVar.add_field(name="/mod seturl", value="Sets the scoring server URL for this server (Manage Server permissions required)", inline=False)
	embedVar.add_field(name="/mod geturl", value="Gets the current scoring server URL for this server", inline=False)
	await interaction.response.send_message(embed=embedVar)


##############################################################################


@tree.command(name="invite", description="Invite Hyperion to your own servers")
async def invite_cmd(interaction: discord.Interaction):
	invite_link = os.environ["INVITE_LINK"]
	button = discord.ui.Button(
		label="Invite me",
		url=invite_link,
		style=discord.ButtonStyle.link
	)

	embedVar = discord.Embed(title="Invite Hyperion", color=0x0d2d43)
	embedVar.add_field(name="Click the button below to invite me to your server!", value="", inline=False)

	view = discord.ui.View()
	view.add_item(button)

	await interaction.response.send_message(embed=embedVar, view=view)


##############################################################################


@tree.command(name="team", description="Fetches a team's information")
async def team_cmd(interaction: discord.Interaction):
    username = interaction.user.name
    pfp_url = interaction.user.display_avatar.url

    with open("server_urls.json", "r") as url_file:
        server_urls = json.load(url_file)

    if str(interaction.guild.id) not in server_urls:
        embedVar = discord.Embed(title="Error", color=0xff0000)
        embedVar.add_field(
            name="No scoring server URL has been set for this server.",
            value="",
            inline=False,
        )
        await interaction.response.send_message(embed=embedVar, ephemeral=True)
        return

    # Common handler
    async def send_team_info(team: str, responder: discord.Interaction):
        output = pull_team(team, responder)
        if output is None:
            embedVar = discord.Embed(title="Team Info", color=0xff0000)
            embedVar.add_field(name="An error occurred.", value="")
            await responder.response.send_message(embed=embedVar, ephemeral=True)
        else:
            overall, tables = output
            embedVar = discord.Embed(title=f"Team Info ({team})", color=0x0d2d43)

            # Pull leaderboard place
            place = "Error"
            for field in pull_leaderboard(responder):
                if team.lower() in field.lower():
                    place = field.strip().split()[0]

            embedVar.add_field(
                name="**Overall**",
                value=f"""<:podium:1324539869438935070> Current Place: {place}
:hourglass: Play Time: {overall[0]}
:dart: Total Score: {overall[1]}""",
            )

            # Prevent going over 25 field limit
            max_fields = 23
            for i, image in enumerate(tables):
                if i >= max_fields:
                    break
                embedVar.add_field(name=f"**{image}**", value=f"```{tables[image]}```", inline=False)

            embedVar.add_field(
                name="", value=f"Generated at: <t:{int(time.time())}:f>", inline=False
            )
            embedVar.set_footer(text=f"Requested by {username}", icon_url=pfp_url)

            await responder.response.send_message(embed=embedVar, ephemeral=False)

    teams = get_all_teams(interaction)

    if len(teams) >= 25:
        # Modal flow
        class TeamModal(discord.ui.Modal, title="Enter Team Name"):
            team_name = discord.ui.TextInput(label="Team Name", placeholder="Enter team name")

            async def on_submit(self, modal_interaction: discord.Interaction):
                await send_team_info(self.team_name.value, modal_interaction)

        await interaction.response.send_modal(TeamModal())

    else:
        # Dropdown flow
        class TeamSelect(discord.ui.Select):
            def __init__(self):
                options = [discord.SelectOption(label=team, value=team) for team in teams]
                super().__init__(placeholder="Choose a team...", options=options)

            async def callback(self, select_interaction: discord.Interaction):
                await send_team_info(self.values[0], select_interaction)

        view = discord.ui.View()
        view.add_item(TeamSelect())

        embedVar = discord.Embed(title="Team Info", color=0x0d2d43)
        embedVar.add_field(
            name="Please select a team to get the information of.",
            value="",
            inline=False,
        )


        await interaction.response.send_message(embed=embedVar, ephemeral=True, view=view)


##############################################################################


@tree.command(name="leaderboard", description="Fetches the current leaderboard")
async def leaderboard_cmd(interaction: discord.Interaction):

	username = interaction.user.name
	pfp_url = interaction.user.display_avatar.url
	
	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	if str(interaction.guild.id) not in server_urls:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="No scoring server URL has been set for this server.", value="", inline=False)
		await interaction.response.send_message(embed=embedVar, ephemeral=True)
		return

	async def leaderboard_select_callback(interaction: discord.Interaction):
		image = select_menu.values[0]

		if image in get_all_images(interaction):
			embedVar = discord.Embed(title=f"<:podium:1324539869438935070>   Leaderboard: {image}", color=0x0d2d43)
			content = image_leaderboard(image, interaction)
			for start_row in range(0, len(content)-1, 15):
				to_add = "\n\n".join(content[start_row:start_row+15])
				embedVar.add_field(name="", value=f"```{to_add}```", inline=False)

			embedVar.add_field(name="", value=f"Generated at: <t:{int(time.time())}:f>", inline=False)
			embedVar.set_footer(text=f"Requested by {username}", icon_url=pfp_url)
			await interaction.response.send_message(embed=embedVar)
		elif image=="Overall":
			embedVar = discord.Embed(title=f"<:podium:1324539869438935070>   Leaderboard: {image}", color=0x0d2d43)
			content = pull_leaderboard(interaction)
			for start_row in range(0, len(content)-1, 15):
				to_add = "\n\n".join(content[start_row:start_row+15])
				embedVar.add_field(name="", value=f"```{to_add}```", inline=False)

			embedVar.add_field(name="", value=f"Generated at: <t:{int(time.time())}:f>", inline=False)
			embedVar.set_footer(text=f"Requested by {username}", icon_url=pfp_url)
			await interaction.response.send_message(embed=embedVar)



	images = ["Overall"] + get_all_images(interaction)

	if not images:
		await interaction.response.send_message("No images available.")
		return


	choices = [discord.SelectOption(label=image, value=image) for image in images]

	select_menu = discord.ui.Select(
		placeholder="Choose an image leaderboard or \"Overall\"...",
		options=choices
	)

	select_menu.callback = leaderboard_select_callback

	embedVar = discord.Embed(title="Leaderboard", color=0x0d2d43)
	embedVar.add_field(name="Please select an image or \"Overall\" to get the leaderboard for.", value="", inline=False)

	await interaction.response.send_message(
		embed=embedVar,
		ephemeral=True,
		view=discord.ui.View().add_item(select_menu)
	)

@modgroup.command(name="seturl", description="Set the scoring server URL for this server.")
@app_commands.describe(newurl="Enter the URL of the scoring server to connect the bot to.")
async def seturl_cmd(interaction: discord.Interaction, newurl: str):
	if not interaction.user.guild_permissions.manage_guild:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="You don't have the required 'Manage Server' permission to use this command.", value="")
		await interaction.response.send_message(
			embed=embedVar,
			ephemeral=True
		)
		return

	# fix newurl
	newurl = newurl.lower()
	newurl = newurl.strip()
	if newurl.startswith("https"):
		newurl = newurl[len("https"):]
	if newurl.startswith("http"):
		newurl = newurl[len("http"):]
	if newurl.startswith("://"):
		newurl = newurl[len("://"):]
	newurl = newurl.rstrip("/")
	newurl = "https://"+newurl+"/"

	if check_no_redirect(newurl):
		with open("server_urls.json", "r") as url_file:
			server_urls = json.load(url_file)
		server_id = str(interaction.guild.id)
		server_urls[server_id] = newurl

		with open("server_urls.json", "w") as url_file:
			json.dump(server_urls, url_file)

		embedVar = discord.Embed(title=f"URL set to {newurl} for this server.", color=0x0d2d43)
		await interaction.response.send_message(embed=embedVar)
	else:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name=f"Invalid URL. Check if there is a typo in {newurl}.", value="")
		await interaction.response.send_message(embed=embedVar, ephemeral=True)

##############################################################################

@modgroup.command(name="geturl", description="Get the current scoring server URL for this server.")
async def geturl_cmd(interaction: discord.Interaction):
	if not interaction.user.guild_permissions.manage_guild:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="You don't have the required 'Manage Server' permission to use this command.",value="")
		await interaction.response.send_message(
			embed=embedVar,
			ephemeral=True
		)
		return
		
	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)

	server_id = str(interaction.guild.id)
	if server_id not in server_urls:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="No URL has been set for this server.",value="")
		await interaction.response.send_message(embed=embedVar, ephemeral=True)
		return
	embedVar = discord.Embed(title="Current URL", color=0x0d2d43)
	embedVar.add_field(name=f"The current URL for this server is: {server_urls[server_id]}", value="")
	await interaction.response.send_message(embed=embedVar)


##############################################################################

tree.add_command(modgroup)

@client.event
async def on_ready():
	await tree.sync()
	print(f'{client.user} is online and active in Discord.')
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="/help for commands"))

##############################################################################

if not os.path.exists("server_urls.json"):
	with open("server_urls.json", "w") as urlsfile:
		urlsfile.write("{}")


token = os.environ['TOKEN']
keep_alive()
start_self_ping()
client.run(token)
