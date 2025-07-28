import discord
from discord.ext import commands
from discord import app_commands
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io

class ProfileView(discord.ui.View):
    def __init__(self, bot, user, guild_id, guild_name):
        super().__init__(timeout=300)
        self.bot = bot
        self.user = user
        self.guild_id = guild_id
        self.guild_name = guild_name
    
    async def create_graph(self, data_type):
        collection = self.bot.db.points if data_type == "points" else self.bot.db.wins
        
        # Get user's data (simplified for speed)
        data = await collection.find(
            {"user_id": self.user.id, "guild_id": self.guild_id}
        ).sort("timestamp", 1).to_list(None)
        
        if not data:
            return None
        
        # Group by date and calculate cumulative
        daily_totals = {}
        for item in data:
            date = item["timestamp"].date()
            daily_totals[date] = daily_totals.get(date, 0) + item["amount"]
        
        dates = sorted(daily_totals.keys())
        cumulative = []
        total = 0
        for date in dates:
            total += daily_totals[date]
            cumulative.append(total)
        
        # Create simple plot
        plt.figure(figsize=(10, 5))
        plt.plot(dates, cumulative, linewidth=2)
        plt.title(f"{self.user.display_name}'s {data_type.title()}")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to bytes
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    @discord.ui.button(label="Points Graph", style=discord.ButtonStyle.primary, emoji="📊")
    async def points_graph(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        graph_buffer = await self.create_graph("points")
        
        if not graph_buffer:
            await interaction.followup.send("No points data found for graph!", ephemeral=True)
            return
        
        file = discord.File(graph_buffer, filename="points_graph.png")
        
        embed = discord.Embed(
            title=f"{self.user.display_name}'s Points Graph",
            color=0x00ff00
        )
        embed.set_image(url="attachment://points_graph.png")
        embed.set_footer(text=f"Server: {self.guild_name}")
        
        await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
    
    @discord.ui.button(label="Wins Graph", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def wins_graph(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        graph_buffer = await self.create_graph("wins")
        
        if not graph_buffer:
            await interaction.followup.send("No wins data found for graph!", ephemeral=True)
            return
        
        file = discord.File(graph_buffer, filename="wins_graph.png")
        
        embed = discord.Embed(
            title=f"{self.user.display_name}'s Wins Graph",
            color=0xffa500
        )
        embed.set_image(url="attachment://wins_graph.png")
        embed.set_footer(text=f"Server: {self.guild_name}")
        
        await interaction.edit_original_response(embed=embed, attachments=[file], view=self)

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="profile", description="Show user profile")
    @app_commands.describe(user="User to show profile for (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        try:
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            target_user = user or interaction.user
            guild_id = interaction.guild.id
            
            # Get user's total points
            points_pipeline = [
                {"$match": {"user_id": target_user.id, "guild_id": guild_id}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            points_result = await self.bot.db.points.aggregate(points_pipeline).to_list(1)
            total_points = points_result[0]["total"] if points_result else 0
            
            # Get user's total wins
            wins_pipeline = [
                {"$match": {"user_id": target_user.id, "guild_id": guild_id}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]
            wins_result = await self.bot.db.wins.aggregate(wins_pipeline).to_list(1)
            total_wins = wins_result[0]["total"] if wins_result else 0
            
            # Get user's cult
            user_cult = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": target_user.id,
                "active": True
            })
            
            # Get user's rank in points
            points_rank_pipeline = [
                {"$match": {"guild_id": guild_id}},
                {"$group": {"_id": "$user_id", "total": {"$sum": "$amount"}}},
                {"$sort": {"total": -1}}
            ]
            points_rankings = await self.bot.db.points.aggregate(points_rank_pipeline).to_list(None)
            points_rank = next((i + 1 for i, rank in enumerate(points_rankings) if rank["_id"] == target_user.id), "N/A")
            
            # Get user's rank in wins
            wins_rank_pipeline = [
                {"$match": {"guild_id": guild_id}},
                {"$group": {"_id": "$user_id", "total": {"$sum": "$amount"}}},
                {"$sort": {"total": -1}}
            ]
            wins_rankings = await self.bot.db.wins.aggregate(wins_rank_pipeline).to_list(None)
            wins_rank = next((i + 1 for i, rank in enumerate(wins_rankings) if rank["_id"] == target_user.id), "N/A")
            
            # Get next points reward
            next_reward = await self.bot.db.reward_roles.find_one({
                "guild_id": guild_id,
                "type": "points",
                "amount": {"$gt": total_points},
                "active": True
            }, sort=[("amount", 1)])
            
            progress_text = ""
            if next_reward:
                progress = total_points / next_reward["amount"]
                filled = int(progress * 10)
                bar = "█" * filled + "░" * (10 - filled)
                role = interaction.guild.get_role(next_reward["role_id"])
                role_name = role.name if role else "Unknown Role"
                progress_text = f"\n\n**Next Reward:** {role_name}\n{bar} {total_points:,.0f}/{next_reward['amount']:,} ({progress*100:.1f}%)"
            
            # Get first activity date
            first_activity = await self.bot.db.points.find_one(
                {"user_id": target_user.id, "guild_id": guild_id},
                sort=[("timestamp", 1)]
            )
            
            # Create embed
            embed = discord.Embed(
                title=f"{target_user.display_name}'s Profile",
                color=0x00ff00
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Basic stats
            embed.add_field(
                name="📊 Stats",
                value=f"**Points:** {total_points:,.0f} (#{points_rank})\n**Wins:** {total_wins:,.0f} (#{wins_rank}){progress_text}",
                inline=True
            )
            
            # Cult info
            cult_text = f"{user_cult['cult_icon']} {user_cult['cult_name']}" if user_cult else "None"
            embed.add_field(
                name="⚔️ Cult",
                value=cult_text,
                inline=True
            )
            

            
            embed.set_footer(text=f"Server: {interaction.guild.name}")
            
            # Create view with graph buttons
            view = ProfileView(self.bot, target_user, guild_id, interaction.guild.name)
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while loading profile!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while loading profile!", ephemeral=True)
            print(f"Error in profile command: {e}")

async def setup(bot):
    await bot.add_cog(Profile(bot))