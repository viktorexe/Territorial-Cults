import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class SetMultiplier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="set_multiplier", description="Set server multiplier (Manage Roles required)")
    @app_commands.describe(multiplier="Multiplier value (1-20)", description="Description for this multiplier event")
    async def set_multiplier(self, interaction: discord.Interaction, multiplier: float, description: str):
        try:
            # Permission check
            if not await check_bot_manager(self.bot, interaction):
                await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
                return
            
            # Validation
            if multiplier < 1 or multiplier > 20:
                await interaction.response.send_message("❌ Multiplier must be between 1 and 20!", ephemeral=True)
                return
            
            if len(description) > 100:
                await interaction.response.send_message("❌ Description must be 100 characters or less!", ephemeral=True)
                return
            
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            guild_id = interaction.guild.id
            
            # Update or insert multiplier setting
            await self.bot.db.multipliers.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        "guild_id": guild_id,
                        "guild_name": interaction.guild.name,
                        "multiplier": multiplier,
                        "description": description,
                        "set_by": interaction.user.id,
                        "set_by_name": str(interaction.user),
                        "timestamp": datetime.now(timezone.utc),
                        "active": True
                    }
                },
                upsert=True
            )
            
            # Create embed
            embed = discord.Embed(
                title="✅ Multiplier Set",
                description=f"Server multiplier set to **{multiplier}x**",
                color=0x00ff00
            )
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Set by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            embed.set_footer(text="Points will now be multiplied by this value")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while setting multiplier!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while setting multiplier!", ephemeral=True)
            print(f"Error in set_multiplier command: {e}")

async def setup(bot):
    await bot.add_cog(SetMultiplier(bot))