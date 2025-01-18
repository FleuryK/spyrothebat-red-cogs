import discord
from redbot.core import commands
import aiohttp

class Osu(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def get_osu_api_credentials(self):
		tokens = await self.bot.get_shared_api_tokens("osu")

		# Ensure the format is correct
		client_id = tokens.get("client_id")
		client_secret = tokens.get("client_secret")

		if not client_id or not client_secret:
			return None, None

		return client_id, client_secret

	async def get_osu_access_token(self, session):
		client_id, client_secret = await self.get_osu_api_credentials()
		if not client_id or not client_secret:
			return None

		token_url = "https://osu.ppy.sh/oauth/token"
		data = {
			"client_id": client_id,
			"client_secret": client_secret,
			"grant_type": "client_credentials",
			"scope": "public"
		}

		async with session.post(token_url, json=data) as response:
			if response.status == 200:
				token_data = await response.json()
				return token_data.get("access_token")
			return None

	@commands.command()
	async def osu(self, ctx, *, username: str):
		"""Fetch OSU! player stats for the given username using API v2 (https://osu.ppy.sh/api/v2/)."""
		client_id, client_secret = await self.get_osu_api_credentials()
		if not client_id or not client_secret:
			await ctx.send("The OSU! API credentials are not set. Please configure them using `[p]set api osu client_id,<client_id> client_secret,<client_secret>`.")
			return

		async with aiohttp.ClientSession() as session:
			access_token = await self.get_osu_access_token(session)
			if not access_token:
				await ctx.send("Unable to retrieve OSU! API access token. Please check your credentials.")
				return

			headers = {
				"Authorization": f"Bearer {access_token}"
			}

			# Fetch user ID
			search_url = f"https://osu.ppy.sh/api/v2/users/{username}"
			async with session.get(search_url, headers=headers) as response:
				if response.status != 200:
					await ctx.send(f"Failed to retrieve user ID for username {username}. Make sure the username is correct.")
					return
				user_data = await response.json()

			user_id = user_data['id']

			# Fetch user data (detailed stats)
			user_url = f"https://osu.ppy.sh/api/v2/users/{user_id}/osu"
			async with session.get(user_url, headers=headers) as response:
				if response.status != 200:
					await ctx.send(f"Failed to retrieve data for user {username}. Make sure the username is correct.")
					return
				user_data = await response.json()

			# Fetch recent activity
			recent_url = f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/recent?limit=1"
			async with session.get(recent_url, headers=headers) as response:
				if response.status != 200:
					await ctx.send(f"No recent plays found for the user {username}.")
					return
				recent_data = await response.json()
				if not recent_data:
					await ctx.send(f"No recent plays found for the user {username}.")
					return
				recent_play = recent_data[0]

			# Fetch beatmap data
			beatmap_url = f"https://osu.ppy.sh/api/v2/beatmaps/{recent_play['beatmap']['id']}"
			async with session.get(beatmap_url, headers=headers) as response:
				if response.status != 200:
					await ctx.send(f"Failed to retrieve beatmap data for the last played map.")
					return
				beatmap = await response.json()

			# Build the embed message
			embed = discord.Embed(title=f"OSU! - Player's statistics for {user_data['username']}", color=discord.Color.from_str("#E966A1"))
			embed.set_thumbnail(url=user_data['avatar_url'])

			embed.add_field(name="Last Played Map", value=f"[{beatmap['beatmapset']['artist']} - {beatmap['beatmapset']['title']}](https://osu.ppy.sh/b/{beatmap['beatmapset']['id']})", inline=False)
			embed.add_field(name="Created by", value=f"{beatmap['beatmapset']['creator']}", inline=False)
			embed.add_field(name="Play Count on Map", value=beatmap['beatmapset']['play_count'], inline=True)
			embed.add_field(name="Rank on Map", value=recent_play['rank'], inline=True)
			embed.add_field(name="Score on Map", value=recent_play['score'], inline=True)
			embed.add_field(name="Max Combo on Map", value=recent_play['max_combo'], inline=True)
			embed.add_field(name="Performance Points (PP) Earned on Map", value=recent_play.get('pp', 'N/A'), inline=True)

			embed.add_field(name="Performance Points (PP)", value=f"{user_data['statistics']['pp']}", inline=True)
			embed.add_field(name="Global Rank", value=f"#{user_data['statistics']['global_rank']}", inline=True)
			embed.add_field(name=f"Country Rank in {user_data['country']['code']}", value=f"#{user_data['statistics']['country_rank']}", inline=True)
			embed.add_field(name="Accuracy", value=f"{user_data['statistics']['hit_accuracy']:.2f}%", inline=True)
			embed.add_field(name="Total Plays", value=user_data['statistics']['play_count'], inline=True)
			embed.add_field(name="Level", value=f"{user_data['statistics']['level']['current']}", inline=True)

			await ctx.send(embed=embed)

async def setup(bot):
	await bot.add_cog(Osu(bot))