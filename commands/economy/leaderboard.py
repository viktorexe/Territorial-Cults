import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
import calendar

class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild_id, guild_name, days=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.guild_name = guild_name
        self.page = 0
        self.mode = "points"  # points or wins
        self.month = None  # None for all time, or (year, month) tuple
        self.days = days  # Days filter
        
    async def get_leaderboard_data(self):
        collection = self.bot.db.points if self.mode == "points" else self.bot.db.wins
        
        # Build match query
        match_query = {"guild_id": self.guild_id}
        
        if self.days is not None:
            now_utc = datetime.now(timezone.utc)
            
            if self.days == 0:
                # Today only (GMT 00:00 - 23:59)
                start_date = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
                end_date = start_date + timedelta(days=1)
                match_query["timestamp"] = {"$gte": start_date, "$lt": end_date}
            else:
                # Last X days (1=today+yesterday, 2=today+yesterday+day before, etc.)
                start_date = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc) - timedelta(days=self.days)
                match_query["timestamp"] = {"$gte": start_date}
        elif self.month:
            year, month = self.month
            start_date = datetime(year, month, 1, tzinfo=timezone.utc)
            if month == 12:
                end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)
            match_query["timestamp"] = {"$gte": start_date, "$lt": end_date}
        
        # Aggregate pipeline
        pipeline = [
            {"$match": match_query},
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
    
    async def get_available_months(self):
        months = set()
        
        for collection in [self.bot.db.points, self.bot.db.wins]:
            pipeline = [
                {"$match": {"guild_id": self.guild_id}},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$timestamp"},
                        "month": {"$month": "$timestamp"}
                    }
                }}
            ]
            
            results = await collection.aggregate(pipeline).to_list(None)
            for result in results:
                months.add((result["_id"]["year"], result["_id"]["month"]))
        
        return sorted(months, reverse=True)
    
    async def update_embed(self, interaction):
        data = await self.get_leaderboard_data()
        
        # Create title with time period info
        if self.days is not None:
            if self.days == 0:
                title = f"{self.mode.title()} Leaderboard - Today (GMT) - {self.guild_name}"
            else:
                title = f"{self.mode.title()} Leaderboard - Last {self.days + 1} days (GMT) - {self.guild_name}"
        else:
            title = f"{self.mode.title()} Leaderboard - All Time - {self.guild_name}"
        
        if not data:
            embed = discord.Embed(
                title=title,
                description="No data found for this period.",
                color=0x2b2d31
            )
        else:
            embed = discord.Embed(
                title=title,
                color=0x00ff00
            )
            
            description = ""
            for i, user_data in enumerate(data, start=self.page * 10 + 1):
                description += f"{i}. <@{user_data['_id']}> - {user_data['total']:,.0f}\n"
            
            embed.description = description
        
        # Update month dropdown
        available_months = await self.get_available_months()
        self.month_select.options = [
            discord.SelectOption(label="All Time", value="all", default=self.month is None)
        ]
        
        for year, month in available_months:
            month_name = calendar.month_name[month]
            label = f"{month_name} {year}"
            value = f"{year}-{month}"
            default = self.month == (year, month)
            self.month_select.options.append(
                discord.SelectOption(label=label, value=value, default=default)
            )
        
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
    
    @discord.ui.select(placeholder="Select month...")
    async def month_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "all":
            self.month = None
        else:
            year, month = map(int, select.values[0].split("-"))
            self.month = (year, month)
        
        self.page = 0
        await self.update_embed(interaction)

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="leaderboard", description="Show server leaderboard")
    @app_commands.describe(days="Days to look back (0=24h, 1=48h, 2=72h, etc. Leave empty for all time)")
    async def leaderboard(self, interaction: discord.Interaction, days: int = None):
        try:
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            view = LeaderboardView(self.bot, interaction.guild.id, interaction.guild.name, days)
            
            # Get initial data
            data = await view.get_leaderboard_data()
            available_months = await view.get_available_months()
            
            # Create title with time period info
            if days is not None:
                if days == 0:
                    title = f"Points Leaderboard - Today (GMT) - {interaction.guild.name}"
                else:
                    title = f"Points Leaderboard - Last {days + 1} days (GMT) - {interaction.guild.name}"
            else:
                title = f"Points Leaderboard - All Time - {interaction.guild.name}"
            
            # Create initial embed
            if not data:
                embed = discord.Embed(
                    title=title,
                    description="No data found.",
                    color=0x2b2d31
                )
            else:
                embed = discord.Embed(
                    title=title,
                    color=0x00ff00
                )
                
                description = ""
                for i, user_data in enumerate(data, 1):
                    description += f"{i}. <@{user_data['_id']}> - {user_data['total']:,.0f}\n"
                
                embed.description = description
            
            # Add footer with time period info
            if days is not None:
                if days == 0:
                    embed.set_footer(text="Today (GMT)")
                else:
                    embed.set_footer(text=f"Last {days + 1} days (GMT)")
            else:
                embed.set_footer(text="All-time")
            
            # Setup month dropdown
            view.month_select.options = [
                discord.SelectOption(label="All Time", value="all", default=True)
            ]
            
            for year, month in available_months:
                month_name = calendar.month_name[month]
                label = f"{month_name} {year}"
                value = f"{year}-{month}"
                view.month_select.options.append(
                    discord.SelectOption(label=label, value=value)
                )
            
            # Update button states
            view.prev_button.disabled = True
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            try:
                await interaction.followup.send("❌ An error occurred while loading leaderboard!", ephemeral=True)
            except:
                pass
            print(f"Error in leaderboard command: {e}")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))