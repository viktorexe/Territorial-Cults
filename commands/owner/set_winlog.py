import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class SetWinlog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="set_winlog", description="Set win log channel")
    @app_commands.describe(
        channel="Channel to monitor for win logs",
        clan_name="Clan name to filter (optional, case insensitive)"
    )
    async def set_winlog(self, interaction: discord.Interaction, channel: discord.TextChannel, clan_name: str = None):
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
            
            # Save/update winlog settings
            settings_data = {
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "channel_id": channel.id,
                "channel_name": channel.name,
                "set_by": interaction.user.id,
                "set_by_name": str(interaction.user),
                "timestamp": datetime.utcnow(),
                "active": True
            }
            
            if clan_name:
                settings_data["clan_name"] = clan_name.strip()
            
            await self.bot.db.winlog_settings.update_one(
                {"guild_id": guild_id},
                {"$set": settings_data},
                upsert=True
            )
            
            # Create embed
            embed = discord.Embed(
                title="✅ Win Log Channel Set",
                description=f"Win logs will be monitored in {channel.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Set by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            
            if clan_name:
                embed.add_field(name="Clan Filter", value=f"Only **{clan_name}** messages", inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while setting win log channel!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while setting win log channel!", ephemeral=True)
            print(f"Error in set_winlog command: {e}")

async def setup(bot):
    await bot.add_cog(SetWinlog(bot))