import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
class BotManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.command(name="bot_manager", description="Configure bot manager role (Admin only)")
    @app_commands.describe(role="Role to set as bot manager")
    async def set_bot_manager(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Administrator permission required!", ephemeral=True)
            return
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        await self.bot.db.bot_settings.update_one(
            {"guild_id": interaction.guild.id},
            {
                "$set": {
                    "guild_id": interaction.guild.id,
                    "manager_role_id": role.id,
                    "manager_role_name": role.name,
                    "set_by": interaction.user.id,
                    "set_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        embed = discord.Embed(
            title="✅ Bot Manager Role Set",
            description=f"Bot manager role set to {role.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)
async def setup(bot):
    await bot.add_cog(BotManager(bot))