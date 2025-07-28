import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta

class CultLeaderboardView(discord.ui.View):
    def __init__(self, bot, guild_id, days=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.page = 0
        self.days = days
        
    async def get_leaderboard_data(self):
        # Get all active cults
        cults = await self.bot.db.cults.find({
            "guild_id": self.guild_id,
            "active": True
        }).to_list(None)
        
        cult_stats = []
        
        for cult in cults:
            total_points = 0
            total_wins = 0
            member_stats = []
            
            # Calculate stats for each member since they joined
            for member_id in cult["members"]:
                # Find earliest record where user was in this cult
                earliest_cult_record = await self.bot.db.points.find_one({
                    "guild_id": self.guild_id,
                    "user_id": member_id,
                    "cult_id": str(cult["_id"])
                }, sort=[("timestamp", 1)])
                
                if earliest_cult_record:
                    member_join_date = earliest_cult_record["timestamp"]
                else:
                    # Check wins collection too
                    earliest_wins_record = await self.bot.db.wins.find_one({
                        "guild_id": self.guild_id,
                        "user_id": member_id,
                        "cult_id": str(cult["_id"])
                    }, sort=[("timestamp", 1)])
                    
                    if earliest_wins_record:
                        member_join_date = earliest_wins_record["timestamp"]
                    else:
                        # Fallback to cult creation date
                        member_join_date = cult["created_at"]
                
                if member_join_date.tzinfo is None:
                    member_join_date = member_join_date.replace(tzinfo=timezone.utc)
                
                # Build time filter - only count records with this cult_id
                time_filter = {
                    "guild_id": self.guild_id, 
                    "user_id": member_id,
                    "cult_id": str(cult["_id"])
                }
                
                if self.days is not None:
                    now_utc = datetime.now(timezone.utc)
                    
                    if self.days == 0:
                        # Today only (GMT 00:00 - 23:59)
                        start_date = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
                        end_date = start_date + timedelta(days=1)
                        # Use the later date between today start and member join date
                        actual_start = max(start_date, member_join_date)
                        time_filter["timestamp"] = {"$gte": actual_start, "$lt": end_date}
                    else:
                        # Last X days (1=today+yesterday, 2=today+yesterday+day before, etc.)
                        start_date = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc) - timedelta(days=self.days)
                        # Use the later date between time filter and member join date
                        actual_start = max(start_date, member_join_date)
                        time_filter["timestamp"] = {"$gte": actual_start}
                else:
                    # All time since member joined cult
                    time_filter["timestamp"] = {"$gte": member_join_date}
                
                # Get member points
                points_result = await self.bot.db.points.aggregate([
                    {"$match": time_filter},
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                ]).to_list(1)
                member_points = points_result[0]["total"] if points_result else 0
                total_points += member_points
                
                # Get member wins
                wins_result = await self.bot.db.wins.aggregate([
                    {"$match": time_filter},
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                ]).to_list(1)
                member_wins = wins_result[0]["total"] if wins_result else 0
                total_wins += member_wins
                
                member_stats.append({
                    "user_id": member_id,
                    "points": member_points,
                    "wins": member_wins
                })
            
            # Get top members
            top_points_member = max(member_stats, key=lambda x: x["points"]) if member_stats else None
            top_wins_member = max(member_stats, key=lambda x: x["wins"]) if member_stats else None
            
            cult_stats.append({
                "cult": cult,
                "total_points": total_points,
                "total_wins": total_wins,
                "top_points_member": top_points_member,
                "top_wins_member": top_wins_member
            })
        
        # Sort by total points
        cult_stats.sort(key=lambda x: x["total_points"], reverse=True)
        
        # Return page data (10 per page)
        start_idx = self.page * 10
        return cult_stats[start_idx:start_idx + 10], len(cult_stats)
    
    async def update_embed(self, interaction):
        data, total_cults = await self.get_leaderboard_data()
        guild = self.bot.get_guild(self.guild_id)
        
        # Create title
        if self.days is not None:
            if self.days == 0:
                title = f"Cult Leaderboard - Today (GMT) - {guild.name}"
                footer_text = "Today (GMT)"
            else:
                title = f"Cult Leaderboard - Last {self.days + 1} days (GMT) - {guild.name}"
                footer_text = f"Last {self.days + 1} days (GMT)"
        else:
            title = f"Cult Leaderboard - All Time - {guild.name}"
            footer_text = "All-time"
        
        embed = discord.Embed(title=title, color=0x00ff00)
        
        # Add time period info
        time_info = ""
        if self.days is not None:
            if self.days == 0:
                time_info = "**Showing for today (GMT 00:00 - 23:59)**\n\n"
            else:
                time_info = f"**Showing for last {self.days + 1} days (GMT 00:00 based)**\n\n"
        
        if not data:
            embed.description = time_info + "No cult data found."
        else:
            description = ""
            start_rank = self.page * 10 + 1
            
            for i, stats in enumerate(data, start_rank):
                cult = stats["cult"]
                description += f"**{i}. {cult['cult_icon']} {cult['cult_name']}**\n"
                description += f"Points: {stats['total_points']:,.0f} | Wins: {stats['total_wins']:,.0f}\n"
                
                if stats["top_points_member"]:
                    description += f"Top Points: <@{stats['top_points_member']['user_id']}> ({stats['top_points_member']['points']:,.0f})\n"
                
                if stats["top_wins_member"]:
                    description += f"Top Wins: <@{stats['top_wins_member']['user_id']}> ({stats['top_wins_member']['wins']:,.0f})\n"
                
                description += "\n"
            
            embed.description = time_info + description
        
        embed.set_footer(text=f"Page {self.page + 1} | {footer_text}")
        
        # Update button states
        self.prev_button.disabled = self.page == 0
        self.next_button.disabled = (self.page + 1) * 10 >= total_cults
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await self.update_embed(interaction)
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await self.update_embed(interaction)

class CultLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="cult_leaderboard", description="Show cult leaderboard")
    @app_commands.describe(days="Days to look back (0=today, 1=yesterday+today, etc. Leave empty for all time)")
    async def cult_leaderboard(self, interaction: discord.Interaction, days: int = None):
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        view = CultLeaderboardView(self.bot, interaction.guild.id, days)
        data, total_cults = await view.get_leaderboard_data()
        
        # Create initial embed
        if days is not None:
            if days == 0:
                title = f"Cult Leaderboard - Today (GMT) - {interaction.guild.name}"
                footer_text = "Today (GMT)"
            else:
                title = f"Cult Leaderboard - Last {days + 1} days (GMT) - {interaction.guild.name}"
                footer_text = f"Last {days + 1} days (GMT)"
        else:
            title = f"Cult Leaderboard - All Time - {interaction.guild.name}"
            footer_text = "All-time"
        
        embed = discord.Embed(title=title, color=0x00ff00)
        
        # Add time period info
        time_info = ""
        if days is not None:
            if days == 0:
                time_info = "**Showing for today (GMT 00:00 - 23:59)**\n\n"
            else:
                time_info = f"**Showing for last {days + 1} days (GMT 00:00 based)**\n\n"
        
        if not data:
            embed.description = time_info + "No cult data found."
        else:
            description = ""
            for i, stats in enumerate(data, 1):
                cult = stats["cult"]
                description += f"**{i}. {cult['cult_icon']} {cult['cult_name']}**\n"
                description += f"Points: {stats['total_points']:,.0f} | Wins: {stats['total_wins']:,.0f}\n"
                
                if stats["top_points_member"]:
                    description += f"Top Points: <@{stats['top_points_member']['user_id']}> ({stats['top_points_member']['points']:,.0f})\n"
                
                if stats["top_wins_member"]:
                    description += f"Top Wins: <@{stats['top_wins_member']['user_id']}> ({stats['top_wins_member']['wins']:,.0f})\n"
                
                description += "\n"
            
            embed.description = time_info + description
        
        embed.set_footer(text=f"Page 1 | {footer_text}")
        
        # Update button states
        view.prev_button.disabled = True
        view.next_button.disabled = total_cults <= 10
        
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CultLeaderboard(bot))