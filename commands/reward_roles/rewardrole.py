import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class RewardRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rewardrole", description="Set milestone reward role (Admin required)")
    @app_commands.describe(
        channel="Channel for notifications",
        reward_type="Points or wins",
        amount="Amount needed",
        role="Role to give"
    )
    @app_commands.choices(reward_type=[
        app_commands.Choice(name="Points", value="points"),
        app_commands.Choice(name="Wins", value="wins")
    ])
    async def rewardrole(self, interaction: discord.Interaction, channel: discord.TextChannel, 
                        reward_type: str, amount: int, role: discord.Role):
        if not await check_bot_manager(self.bot, interaction):
            await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
            return
        
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Role is too high for me to assign!", ephemeral=True)
            return
        
        await self.bot.db.reward_roles.insert_one({
            "guild_id": interaction.guild.id,
            "channel_id": channel.id,
            "role_id": role.id,
            "role_name": role.name,
            "type": reward_type,
            "amount": amount,
            "created_at": datetime.utcnow(),
            "created_by": interaction.user.id,
            "active": True
        })
        
        embed = discord.Embed(
            title="✅ Reward Role Set",
            description=f"Users who reach **{amount:,} {reward_type}** will get {role.mention}",
            color=0x00ff00
        )
        embed.add_field(name="Notifications", value=channel.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RewardRole(bot))