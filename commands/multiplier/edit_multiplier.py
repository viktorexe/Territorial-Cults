import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class EditMultiplier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="edit_multiplier", description="Edit server multiplier (Manage Roles required)")
    @app_commands.describe(multiplier="New multiplier value (1-20)", description="New description for this multiplier event")
    async def edit_multiplier(self, interaction: discord.Interaction, multiplier: float, description: str):
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
            
            # Check if multiplier exists
            existing = await self.bot.db.multipliers.find_one({"guild_id": guild_id, "active": True})
            if not existing:
                await interaction.response.send_message("❌ No active multiplier found! Use `/set_multiplier` first.", ephemeral=True)
                return
            
            old_multiplier = existing["multiplier"]
            
            # Update multiplier
            await self.bot.db.multipliers.update_one(
                {"guild_id": guild_id, "active": True},
                {
                    "$set": {
                        "multiplier": multiplier,
                        "description": description,
                        "edited_by": interaction.user.id,
                        "edited_by_name": str(interaction.user),
                        "edit_timestamp": datetime.utcnow()
                    }
                }
            )
            
            # Create embed
            embed = discord.Embed(
                title="✏️ Multiplier Updated",
                color=0xffa500
            )
            embed.add_field(name="Old Multiplier", value=f"{old_multiplier}x", inline=True)
            embed.add_field(name="New Multiplier", value=f"{multiplier}x", inline=True)
            embed.add_field(name="Description", value=description, inline=False)
            embed.add_field(name="Updated by", value=interaction.user.mention, inline=False)
            embed.set_footer(text="Points will now be multiplied by the new value")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while editing multiplier!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while editing multiplier!", ephemeral=True)
            print(f"Error in edit_multiplier command: {e}")

async def setup(bot):
    await bot.add_cog(EditMultiplier(bot))