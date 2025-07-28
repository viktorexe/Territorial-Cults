import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class Add(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="add", description="Add points to your account")
    @app_commands.describe(points="Points to add (1-1500)")
    async def add(self, interaction: discord.Interaction, points: float):
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
            
            # Get multiplier setting
            multiplier_data = await self.bot.db.multipliers.find_one({"guild_id": guild_id, "active": True})
            multiplier = multiplier_data["multiplier"] if multiplier_data else 1.0
            
            # Calculate final points
            final_points = points * multiplier
            
            # Get user's cult for saving
            user_cult_data = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": user_id,
                "active": True
            })
            
            # Save points transaction
            await self.bot.db.points.insert_one({
                "user_id": user_id,
                "user_name": str(interaction.user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": final_points,
                "base_amount": points,
                "multiplier_used": multiplier,
                "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                "type": "add",
                "timestamp": datetime.now(timezone.utc)
            })
            
            # Save win transaction
            await self.bot.db.wins.insert_one({
                "user_id": user_id,
                "user_name": str(interaction.user),
                "guild_id": guild_id,
                "guild_name": interaction.guild.name,
                "amount": 1,
                "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                "type": "add",
                "timestamp": datetime.now(timezone.utc)
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
            
            user_points = total_points_result[0]["total"] if total_points_result else final_points
            user_wins = total_wins_result[0]["total"] if total_wins_result else 1
            
            # Get user's cult
            user_cult = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": user_id,
                "active": True
            })
            
            cult_text = f"{user_cult['cult_icon']} {user_cult['cult_name']}" if user_cult else "None"
            
            # Create embed
            embed = discord.Embed(color=0x00ff00)
            embed.set_author(
                name=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Build description dynamically
            embed.description = (
                f"{final_points:,.1f} points added to your balance\n"
                f"**New Points:** {user_points:,.1f}\n"
                f"**New Wins:** {user_wins:,}"
            )
            
            if multiplier > 1:
                embed.description += f"\n**Multiplier:** {multiplier}x"
            
            if user_cult:
                embed.description += f"\n**Cult:** {cult_text}"
            
            if multiplier > 1:
                embed.description += f"\n*({points:,.1f} x {multiplier} = {final_points:,.1f})*"
            
            await interaction.response.send_message(embed=embed)
            
            # Trigger reward check
            await self.bot.trigger_reward_check(user_id, guild_id)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while processing your request!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while processing your request!", ephemeral=True)
            print(f"Error in add command: {e}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Add(bot))