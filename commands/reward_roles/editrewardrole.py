import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class EditRewardRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="editrewardrole", description="Edit a reward role (Admin required)")
    @app_commands.describe(
        role="Role to edit",
        new_amount="New amount required",
        new_channel="New notification channel (optional)"
    )
    async def editrewardrole(self, interaction: discord.Interaction, role: discord.Role, 
                           new_amount: int, new_channel: discord.TextChannel = None):
        if not await check_bot_manager(self.bot, interaction):
            await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
            return
        
        if new_amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0!", ephemeral=True)
            return
        
        update_data = {"amount": new_amount}
        if new_channel:
            update_data["channel_id"] = new_channel.id
        
        result = await self.bot.db.reward_roles.update_one(
            {"guild_id": interaction.guild.id, "role_id": role.id, "active": True},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            embed = discord.Embed(
                description=f"Updated reward for {role.mention} to {new_amount:,}" + 
                           (f" with notifications in {new_channel.mention}" if new_channel else ""),
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                description=f"No reward found for {role.mention}",
                color=0xff0000
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EditRewardRole(bot))