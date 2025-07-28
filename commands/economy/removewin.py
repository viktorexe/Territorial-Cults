import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class RemoveWin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="removewin", description="Remove wins from a user (Manage Server required)")
    @app_commands.describe(user="User to remove wins from", wins="Wins to remove")
    async def removewin(self, interaction: discord.Interaction, user: discord.Member, wins: int):
        try:
            # Permission check
            if not await check_bot_manager(self.bot, interaction):
                await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
                return
            
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            user_id = user.id
            guild_id = interaction.guild.id
            
            # Get user's cult
            user_cult_data = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": user_id,
                "active": True
            })
            
            # Save negative wins transaction
            await self.bot.db.wins.insert_one({
                "user_id": user_id,
                "user_name": str(user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": -wins,
                "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                "type": "admin_remove",
                "removed_by": interaction.user.id,
                "timestamp": datetime.utcnow()
            })
            
            embed = discord.Embed(
                title="❌ Wins Removed",
                description=f"Removed {wins:,} wins from {user.mention}",
                color=0xff0000
            )
            embed.add_field(name="Removed by", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while removing wins!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while removing wins!", ephemeral=True)
            print(f"Error in removewin command: {e}")

async def setup(bot):
    await bot.add_cog(RemoveWin(bot))