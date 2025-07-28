import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(color=0x00ff00)
        embed.set_author(
            name=interaction.guild.name,
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        embed.description = (
            "**General Commands**\n"
            "• **/invite** - Get bot invite link and support server\n"
            "• **/help** - Show all available commands\n\n"
            
            "**Economy Commands**\n"
            "• **/add** - Add points to your account\n"
            "• **/remove** - Remove points from your account\n"
            "• **/leaderboard** - Show server leaderboard\n"
            "• **/leaderboard_week** - Show weekly leaderboard\n"
            "• **/profile** - Show user profile\n"
            "• **/rolelist** - Show all reward roles\n\n"
            
            "**Cult Commands**\n"
            "• **/cult_create** - Create a new cult (Bot Manager)\n"
            "• **/cult_list** - List all cults with join/leave buttons\n"
            "• **/edit_cult** - Edit cult information (Bot Manager)\n"
            "• **/join_cult** - Join a cult\n"
            "• **/cult_info** - Show detailed cult information\n"
            "• **/cult_stats** - Show cult stats and war history\n"
            "• **/cult_leaderboard** - Show cult leaderboard with time filters\n"
            "• **/promote_member** - Promote member to officer (Leaders only)\n\n"
            
            "**Cult Wars & Alliances**\n"
            "• **/cult_war** - Declare war on another cult (Leaders/Officers)\n"
            "• **/end_war** - End your cult's war (Leaders/Officers)\n"
            "• **/cult_alliance** - Propose alliance (Leaders only)\n"
            "• **/end_alliance** - End alliance (Leaders only)\n\n"
            
            "**Bot Manager Commands** (Bot Manager role required)\n"
            "• **/bot_manager** - Set bot manager role (Admin only)\n"
            "• **/addscore** - Add points to a user\n"
            "• **/addwin** - Add wins to a user\n"
            "• **/removescore** - Remove points from a user\n"
            "• **/removewin** - Remove wins from a user\n"
            "• **/set_multiplier** - Set server multiplier\n"
            "• **/edit_multiplier** - Edit server multiplier\n"
            "• **/end_multiplier** - End server multiplier\n"
            "• **/multiplier_info** - Show multiplier information\n"
            "• **/rewardrole** - Set up reward roles\n"
            "• **/deletereward** - Delete reward role\n"
            "• **/editrewardrole** - Edit reward role\n"
            "• **/listrewards** - List reward settings\n"
            "• **/debug_rewards** - Debug reward system\n"
            "• **/force_refresh_rewards** - Force refresh reward roles\n"
            "• **/cleanup_roles** - Remove duplicate milestone roles\n"
            "• **/set_winlog** - Set win log channel\n\n"
            
            "**Useful Links**\n"
            "• Bot Guide: https://territorialcults.vercel.app\n"
            "• Terms of Service: https://territorialcultstos.vercel.app\n"
            "• Privacy Policy: https://territorialcultsprivacy.vercel.app"
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))