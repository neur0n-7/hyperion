import os
import io
import requests
import datetime
import json
import time
import sys

import discord
from discord import app_commands
from table2ascii import PresetStyle
from table2ascii import table2ascii as t2a
from bs4 import BeautifulSoup

from keep_alive import keep_alive, start_self_ping

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

execute_access_attempts = {}
execute_access_timeouts = {}

def get_time(code):
	return(datetime.datetime.now().strftime("%"+code))


def current_time():
	month = get_time('B')
	year = get_time('Y')
	hour = get_time('I')
	minute = get_time('M')
	am_pm = get_time('p')
	second = get_time('S')
	dayofweek = get_time('A')
	date = get_time('d')
	date = (dayofweek+', '+month+ ' '+date+', '+year)
	return (hour+':'+minute+':'+second+' '+am_pm)


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


@client.event
async def on_ready():
	await tree.sync()
	print(f'{client.user} is online and active in Discord.')
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="/help for commands"))


@tree.command(name="ping", description="Checks if Hyperion is online")
async def ping_cmd(interaction: discord.Interaction):
	latency = round(interaction.client.latency * 1000)
	embedVar = discord.Embed(
		title=":white_check_mark:   Pong!",
		description=f"Hyperion is online.\nPing: {latency}ms",
		color=0x0d2d43
	)
	await interaction.response.send_message(embed=embedVar)


@tree.command(name="help", description="List all Hyperion commands")
async def help_cmd(interaction: discord.Interaction):
	embedVar = discord.Embed(title="Help", color=0x0d2d43)
	embedVar.add_field(name="/help", value="List all Hyperion commands", inline=False)
	embedVar.add_field(name="/ping", value="Checks if Hyperion is online", inline=False)
	embedVar.add_field(name="/leaderboard", value="Fetches the current leaderboard- overall or for a specific image", inline=False)
	embedVar.add_field(name="/team", value="Fetches a team's information", inline=False)
	embedVar.add_field(name="/seturl", value="Sets the scoring server URL for this server (Manage Server permissions required)", inline=False)
	embedVar.add_field(name="/geturl", value="Gets the current scoring server URL for this server", inline=False)
	embedVar.add_field(name="/invite", value="Invite Hyperion to your own server", inline=False)
	embedVar.add_field(name="", value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=True)
	await interaction.response.send_message(embed=embedVar)

@tree.command(name="invite", description="Invite Hyperion to your own servers")
async def invite_cmd(interaction: discord.Interaction):
	invite_link = os.environ["INVITE_LINK"]
	button = discord.ui.Button(
		label="Invite me",
		url=invite_link,
		style=discord.ButtonStyle.link
	)

	embedVar = discord.Embed(title="Invite Hyperion", color=0x0d2d43)
	embedVar.add_field(name="Click the button below to invite me to your server!",
			   value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", 
			   inline=False)

	view = discord.ui.View()
	view.add_item(button)

	await interaction.response.send_message(embed=embedVar, view=view)

@tree.command(name="team", description="Fetches a team's information")
async def team_cmd(interaction: discord.Interaction):

	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	if str(interaction.guild.id) not in server_urls:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="No scoring server URL has been set for this server.", 
					 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
		await interaction.response.send_message(embed=embedVar, ephemeral=True)
		return


	async def team_select_callback(interaction: discord.Interaction):
		team = select_menu.values[0]

		output = pull_team(team, interaction)
		if output is None:
			embedVar = discord.Embed(title="Team Info", color=0xff0000)
			embedVar.add_field(name="An error occured.",
					  value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
		else:
			overall, tables = output
			embedVar = discord.Embed(title=f"Team Info ({team})", color=0x0d2d43)
			place = "Error"
			for field in pull_leaderboard(interaction):
				if team.lower() in field.lower():
					place = field.strip().split()[0]
			embedVar.add_field(name="**Overall**", value=f"""<:podium:1324539869438935070> Current Place: {place}
	:hourglass: Play Time: {overall[0]}
	:dart: Total Score: {overall[1]}
			""")
			for image in tables:
				embedVar.add_field(name=f"**{image}**", value=f"```{tables[image]}```", inline=False)
			embedVar.add_field(name="", value=f"Generated at: {current_time()}", inline=False)
			embedVar.add_field(name="", value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
		await interaction.response.send_message(embed=embedVar)

	teams = get_all_teams(interaction)
	choices = [discord.SelectOption(label=team, value=team) for team in teams]

	select_menu = discord.ui.Select(
		placeholder="Choose a team...",
		options=choices
	)

	select_menu.callback = team_select_callback 

	embedVar = discord.Embed(title="Team Info", color=0x0d2d43)
	embedVar.add_field(name="Please select a team to get the information of.", 
					value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)

	await interaction.response.send_message(
		embed=embedVar,
		ephemeral=True,
		view=discord.ui.View().add_item(select_menu)
	)


@tree.command(name="leaderboard", description="Fetches the current leaderboard")
async def leaderboard_cmd(interaction: discord.Interaction):

	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)
	if str(interaction.guild.id) not in server_urls:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="No scoring server URL has been set for this server.", 
					 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
		await interaction.response.send_message(embed=embedVar, ephemeral=True)
		return

	async def leaderboard_select_callback(interaction: discord.Interaction):
		image = select_menu.values[0]

		if image in get_all_images(interaction):
			embedVar = discord.Embed(title=f"<:podium:1324539869438935070>   Leaderboard: {image}", color=0x0d2d43)
			content = "\n\n".join(image_leaderboard(image, interaction)[:19])
			embedVar.add_field(name="", value=f"```{content}```", inline=False)
			embedVar.add_field(name="", value=f"Generated at: {current_time()}\n-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
			await interaction.response.send_message(embed=embedVar)
		elif image=="Overall":
			embedVar = discord.Embed(title=f"<:podium:1324539869438935070>   Leaderboard: {image}", color=0x0d2d43)
			content = "\n\n".join(pull_leaderboard(interaction)[:19])
			embedVar.add_field(name="", value=f"```{content}```", inline=False)
			embedVar.add_field(name="", value=f"Generated at: {current_time()}\n-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)
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
	embedVar.add_field(name="Please select an image or \"Overall\" to get the leaderboard for.", 
					value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>", inline=False)

	await interaction.response.send_message(
		embed=embedVar,
		ephemeral=True,
		view=discord.ui.View().add_item(select_menu)
	)


@tree.command(name="seturl", description="Set the scoring server URL for this server.")
@app_commands.describe(newurl="Enter the URL of the scoring server to connect the bot to.")
async def seturl_cmd(interaction: discord.Interaction, newurl: str):
	if not interaction.user.guild_permissions.manage_guild:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="You don't have the required 'Manage Server' permission to use this command.",
					 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
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
		embedVar.add_field(name="", value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
		await interaction.response.send_message(embed=embedVar)
	else:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name=f"Invalid URL. Check if there is a typo in {newurl}.",
					 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
		await interaction.response.send_message(embed=embedVar, ephemeral=True)

@tree.command(name="geturl", description="Get the current scoring server URL for this server.")
async def geturl_cmd(interaction: discord.Interaction):

	with open("server_urls.json", "r") as url_file:
		server_urls = json.load(url_file)

	server_id = str(interaction.guild.id)
	if server_id not in server_urls:
		embedVar = discord.Embed(title="Error", color=0xff0000)
		embedVar.add_field(name="No URL has been set for this server.",
					 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
		await interaction.response.send_message(embed=embedVar, ephemeral=True)
		return
	embedVar = discord.Embed(title="Current URL", color=0x0d2d43)
	embedVar.add_field(name=f"The current URL for this server is: {server_urls[server_id]}",
					value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
	await interaction.response.send_message(embed=embedVar)

modpanel_group = app_commands.Group(name="modpanel", description="Hyperion mod commands")

@modpanel_group.command(name="execute", description="Execute Python command on Hyperion console")
async def modpanel_execute(interaction: discord.Interaction, cmd: str, passwd: str):
	userid = interaction.user.id

	# user is timed out
	if userid in execute_access_timeouts.keys():
		# check if timeout has expired
		if time.time()-execute_access_timeouts[userid]>=300:
			del execute_access_timeouts[userid]
		else:
			embedVar = discord.Embed(title="Error", color=0xff0000)
			embedVar.add_field(name=f"You are on a timeout. Please try again in **{round(execute_access_timeouts[userid]-time.time(), 1)}** seconds.",
						 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
			await interaction.response.send_message(embed=embedVar, ephemeral=True)
			return
	else:
		if passwd==os.environ["MODPANEL_PASSWD"]:
			# passwd correct
			execute_access_attempts[userid]=0

			old_stdout = sys.stdout
			sys.stdout = io.StringIO()
			try:
				exec(cmd)
				output = sys.stdout.getvalue()[230]
			except Exception as error:
				output = (None, error)[230]
			finally:
				sys.stdout = old_stdout
			embedVar = discord.Embed(title="Execution Output", color=0x0d2d43)
			if isinstance(output, tuple) and output[0] is None:
				embedVar.add_field(name=f"**Execution error**: ```{output[1]}```",
						 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
			else:
				embedVar.add_field(name=f"```{output}```",
							 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")

			await interaction.response.send_message(embed=embedVar, ephemeral=True)
			
		else:
			# passwd incorrect
			if userid in execute_access_attempts.keys():
				execute_access_attempts[userid]+=1
			else:
				execute_access_attempts[userid]=1
				
			if execute_access_attempts[userid]>=3:
				embedVar = discord.Embed(title="Timed out", color=0xff0000)
				embedVar.add_field(name="You cannot enter any more modpanel passwords for the next 10 minutes.",
						 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
			else:
				embedVar = discord.Embed(title="Incorrect password", color=0xff0000)
				embedVar.add_field(name=f"You have **{3-execute_access_attempts[userid]}** attempts remaining.",
						 value="-# Hyperion - Sarpedon Scoring Server Discord Bot  <:hyperion:1324540054349152279>")
			await interaction.response.send_message(embed=embedVar, ephemeral=True)

tree.add_command(modpanel_group)

@client.event
async def on_ready():
	await tree.sync()
	print("Logged in and ready")

#######################

if not os.path.exists("server_urls.json"):
	with open("server_urls.json", "w") as urlsfile:
		urlsfile.write("{}")


token = os.environ['TOKEN']
keep_alive()
start_self_ping()
client.run(token)
