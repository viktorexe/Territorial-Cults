import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta

class LeaderboardWeekView(discord.ui.View):
    def __init__(self, bot, guild_id, guild_name):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.page = 0
        self.mode = "points"  # points or wins
        
    async def get_leaderboard_data(self):
        collection = self.bot.db.points if self.mode == "points" else self.bot.db.wins
        
        # Get data from last 7 days
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Aggregate pipeline
        pipeline = [
            {"$match": {
                "guild_id": self.guild_id,
                "timestamp": {"$gte": week_ago}
            }},
            {"$group": {
                "_id": "$user_id",
                "user_name": {"$last": "$user_name"},
                "total": {"$sum": "$amount"}
            }},
            {"$sort": {"total": -1}},
            {"$skip": self.page * 10},
            {"$limit": 10}
        ]
        
        return await collection.aggregate(pipeline).to_list(10)
    
    async def update_embed(self, interaction):
        data = await self.get_leaderboard_data()
        
        if not data:
            embed = discord.Embed(
                title=f"Showing {self.mode} leaderboard for {self.guild_name} (Last 7 Days)",
                description="No data found for the last 7 days.",
                color=0x2b2d31
            )
        else:
            embed = discord.Embed(
                title=f"Showing {self.mode} leaderboard for {self.guild_name} (Last 7 Days)",
                color=0x00ff00
            )
            
            description = ""
            for i, user_data in enumerate(data, start=self.page * 10 + 1):
                description += f"{i}. <@{user_data['_id']}> - {user_data['total']:,.0f}\n"
            
            embed.description = description
        
        # Update button states
        self.prev_button.disabled = self.page == 0
        self.wins_button.label = "Points" if self.mode == "wins" else "Wins"
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await self.update_embed(interaction)
    
    @discord.ui.button(label="Wins", style=discord.ButtonStyle.primary)
    async def wins_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mode = "wins" if self.mode == "points" else "points"
        self.page = 0
        await self.update_embed(interaction)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_embed(interaction)

class LeaderboardWeek(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="leaderboard_week", description="Show server leaderboard for last 7 days")
    async def leaderboard_week(self, interaction: discord.Interaction):
        try:
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            view = LeaderboardWeekView(self.bot, interaction.guild.id, interaction.guild.name)
            
            # Get initial data
            data = await view.get_leaderboard_data()
            
            # Create initial embed
            if not data:
                embed = discord.Embed(
                    title=f"Showing points leaderboard for {interaction.guild.name} (Last 7 Days)",
                    description="No data found for the last 7 days.",
                    color=0x2b2d31
                )
            else:
                embed = discord.Embed(
                    title=f"Showing points leaderboard for {interaction.guild.name} (Last 7 Days)",
                    color=0x00ff00
                )
                
                description = ""
                for i, user_data in enumerate(data, 1):
                    description += f"{i}. <@{user_data['_id']}> - {user_data['total']:,.0f}\n"
                
                embed.description = description
            
            # Update button states
            view.prev_button.disabled = True
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            try:
                await interaction.followup.send("❌ An error occurred while loading weekly leaderboard!", ephemeral=True)
            except:
                pass
            print(f"Error in leaderboard_week command: {e}")

async def setup(bot):
    await bot.add_cog(LeaderboardWeek(bot))