import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class AddScore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="addscore", description="Add points to a user (Manage Server required)")
    @app_commands.describe(user="User to add points to", points="Points to add")
    async def addscore(self, interaction: discord.Interaction, user: discord.Member, points: float):
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
            
            # Save points transaction
            await self.bot.db.points.insert_one({
                "user_id": user_id,
                "user_name": str(user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": points,
                "base_amount": points,
                "multiplier_used": 1.0,
                "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                "type": "admin_add",
                "added_by": interaction.user.id,
                "timestamp": datetime.utcnow()
            })
            
            embed = discord.Embed(
                title="✅ Points Added",
                description=f"Added {points:,.1f} points to {user.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Added by", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
            # Trigger reward check
            await self.bot.trigger_reward_check(user_id, guild_id)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while adding points!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while adding points!", ephemeral=True)
            print(f"Error in addscore command: {e}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(AddScore(bot))