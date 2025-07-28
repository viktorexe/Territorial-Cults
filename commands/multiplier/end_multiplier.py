import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class EndMultiplier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="end_multiplier", description="End server multiplier (Manage Roles required)")
    async def end_multiplier(self, interaction: discord.Interaction):
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
            
            guild_id = interaction.guild.id
            
            # Check if multiplier exists
            existing = await self.bot.db.multipliers.find_one({"guild_id": guild_id, "active": True})
            if not existing:
                await interaction.response.send_message("❌ No active multiplier found!", ephemeral=True)
                return
            
            old_multiplier = existing["multiplier"]
            
            # Deactivate multiplier
            await self.bot.db.multipliers.update_one(
                {"guild_id": guild_id, "active": True},
                {
                    "$set": {
                        "active": False,
                        "ended_by": interaction.user.id,
                        "ended_by_name": str(interaction.user),
                        "end_timestamp": datetime.utcnow()
                    }
                }
            )
            
            # Create embed
            embed = discord.Embed(
                title="🛑 Multiplier Ended",
                description=f"Server multiplier ({old_multiplier}x) has been deactivated",
                color=0xff0000
            )
            embed.add_field(name="Ended by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            embed.set_footer(text="Points will now be added at normal rate (1x)")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while ending multiplier!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while ending multiplier!", ephemeral=True)
            print(f"Error in end_multiplier command: {e}")

async def setup(bot):
    await bot.add_cog(EndMultiplier(bot))