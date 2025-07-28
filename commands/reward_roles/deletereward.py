import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class DeleteReward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def reward_role_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.guild or self.bot.db is None:
            return []
        
        rewards = await self.bot.db.reward_roles.find({
            "guild_id": interaction.guild.id,
            "active": True
        }).to_list(25)
        
        choices = []
        for reward in rewards:
            role = interaction.guild.get_role(reward["role_id"])
            if role and current.lower() in role.name.lower():
                choices.append(app_commands.Choice(
                    name=f"{role.name} ({reward['amount']:,} {reward['type']})",
                    value=str(role.id)
                ))
        
        return choices
    
    @app_commands.command(name="deletereward", description="Delete a reward role (Admin required)")
    @app_commands.describe(role="Role to remove from rewards")
    @app_commands.autocomplete(role=reward_role_autocomplete)
    async def deletereward(self, interaction: discord.Interaction, role: str):
        if not await check_bot_manager(self.bot, interaction):
            await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
            return
        
        try:
            role_id = int(role)
            role_obj = interaction.guild.get_role(role_id)
            
            if not role_obj:
                await interaction.response.send_message("❌ Role not found!", ephemeral=True)
                return
            
            result = await self.bot.db.reward_roles.delete_one({
                "guild_id": interaction.guild.id,
                "role_id": role_id,
                "active": True
            })
            
            if result.deleted_count > 0:
                embed = discord.Embed(
                    description=f"Removed reward for {role_obj.mention}",
                    color=0xff0000
                )
            else:
                embed = discord.Embed(
                    description=f"No reward found for {role_obj.mention}",
                    color=0xff0000
                )
        except ValueError:
            await interaction.response.send_message("❌ Invalid role!", ephemeral=True)
            return
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DeleteReward(bot))