import discord
from redbot.core import commands
import aiohttp

class ScoreSaber(commands.Cog):
	"""Cog for interacting with the ScoreSaber API."""

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def scoresaber(self, ctx, *, username: str):
		"""Fetch ScoreSaber profile data for a user by username.

		Parameters:
		- username: The ScoreSaber username of the user.
		"""
		search_url = "https://scoresaber.com/api/players?search="

		# Replace spaces in the username with %20
		username = username.replace(" ", "%20")

		async with aiohttp.ClientSession() as session:
			# Step 1: Get user ID by username
			async with session.get(f"{search_url}{username}") as search_response:
				if search_response.status != 200:
					return await ctx.send("An error occurred while searching for the user. Check the nickname.")

				search_data = await search_response.json()

				if not search_data or not search_data.get('players'):
					return await ctx.send("No users found with this nickname.")

				user_id = search_data['players'][0]['id']

			# Step 2: Fetch user profile data by ID
			profile_url = f"https://scoresaber.com/api/player/{user_id}/full"
			async with session.get(profile_url) as profile_response:
				if profile_response.status != 200:
					return await ctx.send("An error occurred while retrieving profile data.")

				data = await profile_response.json()

			# Step 3: Fetch recent score data
			recent_scores_url = f"https://scoresaber.com/api/player/{user_id}/scores?sort=recent&limit=1"
			async with session.get(recent_scores_url) as recent_scores_response:
				if recent_scores_response.status != 200:
					return await ctx.send("An error occurred while retrieving recent scores.")

				recent_scores_data = await recent_scores_response.json()
				last_score = recent_scores_data['playerScores'][0] if recent_scores_data and 'playerScores' in recent_scores_data else None

		try:
			# Extracting user data
			name = data['name']
			profile_picture = data['profilePicture']
			rank_global = data['rank']
			rank_country = data['countryRank']
			country = data['country']
			total_score = data['scoreStats']['totalScore']
			total_ranked_score = data['scoreStats']['totalRankedScore']
			total_plays = data['scoreStats']['totalPlayCount']
			ranked_plays = data['scoreStats']['rankedPlayCount']
			performance_points = data['pp']

			# Extracting last score data
			if last_score:
				last_map_name = last_score['leaderboard']['songName']
				last_map_author = last_score['leaderboard']['levelAuthorName']
				difficulty_mapping = {
					1: "Easy",
					3: "Normal",
					5: "Hard",
					7: "Expert",
					9: "Expert+"
				}
				last_map_difficulty = difficulty_mapping.get(last_score['leaderboard']['difficulty']['difficulty'], "Unknown")
				last_map_score = last_score['score']['baseScore']
			else:
				last_map_name = "None"
				last_map_author = "None"
				last_map_difficulty = "None"
				last_map_score = "None"

			# Create an embed message
			embed = discord.Embed(title=f"ScoreSaber profile of {name}", color=discord.Color.pink())
			embed.set_thumbnail(url=profile_picture)

			embed.add_field(name="International rank", value=f"#{rank_global}", inline=True)
			embed.add_field(name=f"National rank in {country}", value=f"#{rank_country}", inline=True)
			embed.add_field(name="Total score", value=f"{total_score:,}", inline=True)
			embed.add_field(name="Total score in Ranked", value=f"{total_ranked_score:,}", inline=True)
			embed.add_field(name="Number of times played", value=f"{total_plays}", inline=True)
			embed.add_field(name="Number of times played in Ranked", value=f"{ranked_plays}", inline=True)
			embed.add_field(name="Points of Performance (PP)", value=f"{performance_points}", inline=True)

			if last_score:
				embed.add_field(name="Last Played Map", value=last_map_name, inline=False)
				embed.add_field(name="Creator of the Map", value=last_map_author, inline=True)
				embed.add_field(name="Difficulty", value=last_map_difficulty, inline=True)
				embed.add_field(name="Score", value=f"{last_map_score:,}", inline=True)

			await ctx.send(embed=embed)

		except KeyError:
			await ctx.send("Unable to retrieve certain information for this user.")

async def setup(bot):
	await bot.add_cog(ScoreSaber(bot))