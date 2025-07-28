import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class EndAlliance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def alliance_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.guild or self.bot.db is None:
            return []
        
        # Find user's cult
        user_cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_leader_id": interaction.user.id,
            "active": True
        })
        
        if not user_cult:
            return []
        
        # Get alliances
        alliances = await self.bot.db.cult_alliances.find({
            "$or": [
                {"cult1_id": str(user_cult["_id"])},
                {"cult2_id": str(user_cult["_id"])}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        }).to_list(25)
        
        choices = []
        for alliance in alliances:
            if alliance["cult1_id"] == str(user_cult["_id"]):
                ally_name = alliance["cult2_name"]
            else:
                ally_name = alliance["cult1_name"]
            
            if current.lower() in ally_name.lower():
                choices.append(app_commands.Choice(name=ally_name, value=ally_name))
        
        return choices
    
    @app_commands.command(name="end_alliance", description="End alliance with another cult (Leaders only)")
    @app_commands.describe(ally_cult="Allied cult to end alliance with")
    @app_commands.autocomplete(ally_cult=alliance_autocomplete)
    async def end_alliance(self, interaction: discord.Interaction, ally_cult: str):
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        # Find user's cult where they are leader
        user_cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_leader_id": interaction.user.id,
            "active": True
        })
        
        if not user_cult:
            await interaction.response.send_message("❌ You must be a cult leader to end alliances!", ephemeral=True)
            return
        
        # Find the alliance
        alliance = await self.bot.db.cult_alliances.find_one({
            "$or": [
                {"cult1_id": str(user_cult["_id"]), "cult2_name": ally_cult},
                {"cult2_id": str(user_cult["_id"]), "cult1_name": ally_cult}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if not alliance:
            await interaction.response.send_message("❌ No active alliance found with this cult!", ephemeral=True)
            return
        
        # End the alliance
        await self.bot.db.cult_alliances.update_one(
            {"_id": alliance["_id"]},
            {
                "$set": {
                    "active": False,
                    "ended_by": interaction.user.id,
                    "ended_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Create announcement embed
        embed = discord.Embed(
            title="💔 Alliance Ended",
            description=f"The alliance between {user_cult['cult_icon']} **{user_cult['cult_name']}** and **{ally_cult}** has been ended.",
            color=0xff0000
        )
        embed.add_field(name="Ended by", value=interaction.user.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EndAlliance(bot))