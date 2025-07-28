import discord
from discord.ext import commands
from discord import app_commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="invite", description="Get bot invite link and support server")
    async def invite(self, interaction: discord.Interaction):
        embed = discord.Embed(color=0x00ff00)
        embed.description = (
            "**Invite me** - [Click Here](https://discord.com/oauth2/authorize?client_id=1391449407299260456)\n"
            "**Support Server** - [Join Here](https://discord.gg/HvF5QnqtHN)"
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Invite(bot))