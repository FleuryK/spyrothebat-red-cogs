from .scoresaber import ScoreSaber


async def setup(bot):
	await bot.add_cog(ScoreSaber(bot))