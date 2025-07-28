import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class Remove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="remove", description="Remove points from your account")
    @app_commands.describe(points="Points to remove (1-1500)")
    async def remove(self, interaction: discord.Interaction, points: float):
        try:
            # Validation
            if points < 1 or points > 1500:
                await interaction.response.send_message("❌ Points must be between 1 and 1500!", ephemeral=True)
                return
            
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            user_id = interaction.user.id
            guild_id = interaction.guild.id
            
            # Save negative points transaction
            await self.bot.db.points.insert_one({
                "user_id": user_id,
                "user_name": str(interaction.user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": -points,
                "type": "remove",
                "timestamp": datetime.utcnow()
            })
            
            # Get user's cult for saving
            user_cult_data = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": user_id,
                "active": True
            })
            
            # Save negative win transaction
            await self.bot.db.wins.insert_one({
                "user_id": user_id,
                "user_name": str(interaction.user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": -1,
                "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                "type": "remove",
                "timestamp": datetime.utcnow()
            })
            
            # Get server-specific totals
            points_pipeline = [
                {"$match": {"user_id": user_id, "guild_id": guild_id}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            
            wins_pipeline = [
                {"$match": {"user_id": user_id, "guild_id": guild_id}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            
            total_points_result = await self.bot.db.points.aggregate(points_pipeline).to_list(1)
            total_wins_result = await self.bot.db.wins.aggregate(wins_pipeline).to_list(1)
            
            user_points = total_points_result[0]["total"] if total_points_result else -points
            user_wins = total_wins_result[0]["total"] if total_wins_result else -1
            
            # Create embed
            embed = discord.Embed(color=0xff0000)
            embed.set_author(
                name=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            embed.description = (
                f"{points:,.1f} points removed from your balance\n"
                f"**New Points:** {user_points:,.1f}\n"
                f"**New Wins:** {user_wins:,}\n"
                f"**Multiplier:** Coming Soon\n"
                f"**Cult:** Coming Soon"
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while processing your request!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while processing your request!", ephemeral=True)
            print(f"Error in remove command: {e}")

async def setup(bot):
    await bot.add_cog(Remove(bot))