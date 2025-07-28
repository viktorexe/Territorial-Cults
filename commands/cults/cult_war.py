import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
import re

class CultWar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cult_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.guild or self.bot.db is None:
            return []
        
        # Get user's cult to exclude it
        user_cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "members": interaction.user.id,
            "active": True
        })
        
        # Get all other cults
        query = {"guild_id": interaction.guild.id, "active": True}
        if user_cult:
            query["_id"] = {"$ne": user_cult["_id"]}
        
        cults = await self.bot.db.cults.find(query).to_list(25)
        
        return [
            app_commands.Choice(name=f"{cult['cult_icon']} {cult['cult_name']}", value=cult['cult_name'])
            for cult in cults
            if current.lower() in cult['cult_name'].lower()
        ]
    
    def parse_duration(self, duration_str):
        """Parse duration string like 10s, 5m, 2h, 1d"""
        match = re.match(r'^(\d+)([smhd])$', duration_str.lower())
        if not match:
            return None
        
        amount, unit = match.groups()
        amount = int(amount)
        
        if unit == 's':
            return timedelta(seconds=amount)
        elif unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        
        return None
    
    @app_commands.command(name="cult_war", description="Declare war on another cult (Leaders/Officers only)")
    @app_commands.describe(
        target_cult="Cult to declare war on",
        duration="War duration (e.g., 10s, 5m, 2h, 1d)",
        race_type="Type of competition"
    )
    @app_commands.choices(race_type=[
        app_commands.Choice(name="Points Race", value="points"),
        app_commands.Choice(name="Wins Race", value="wins"),
        app_commands.Choice(name="Both Points & Wins", value="both")
    ])
    @app_commands.autocomplete(target_cult=cult_autocomplete)
    async def cult_war(self, interaction: discord.Interaction, target_cult: str, duration: str, race_type: str = "points"):
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        # Find user's cult
        user_cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "members": interaction.user.id,
            "active": True
        })
        
        if not user_cult:
            await interaction.response.send_message("❌ You must be in a cult to declare war!", ephemeral=True)
            return
        
        # Check if user is leader or officer
        is_leader = user_cult["cult_leader_id"] == interaction.user.id
        is_officer = False
        
        if user_cult.get("officer_role_id"):
            officer_role = interaction.guild.get_role(user_cult["officer_role_id"])
            is_officer = officer_role and officer_role in interaction.user.roles
        
        if not (is_leader or is_officer):
            await interaction.response.send_message("❌ Only cult leaders and officers can declare war!", ephemeral=True)
            return
        
        # Parse duration
        duration_delta = self.parse_duration(duration)
        if not duration_delta:
            await interaction.response.send_message("❌ Invalid duration format! Use: 10s, 5m, 2h, 1d", ephemeral=True)
            return
        
        # Find target cult
        target = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_name": target_cult,
            "active": True
        })
        
        if not target:
            await interaction.response.send_message("❌ Target cult not found!", ephemeral=True)
            return
        
        # Check if user's cult is already in any war
        existing_war = await self.bot.db.cult_wars.find_one({
            "$or": [
                {"attacker_cult_id": str(user_cult["_id"])},
                {"defender_cult_id": str(user_cult["_id"])}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if existing_war:
            await interaction.response.send_message("❌ Your cult is already in a war!", ephemeral=True)
            return
        
        # Check if target cult is already in any war
        target_war = await self.bot.db.cult_wars.find_one({
            "$or": [
                {"attacker_cult_id": str(target["_id"])},
                {"defender_cult_id": str(target["_id"])}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if target_war:
            await interaction.response.send_message("❌ Target cult is already in a war!", ephemeral=True)
            return
        
        # Check if cults are allied
        alliance = await self.bot.db.cult_alliances.find_one({
            "$or": [
                {"cult1_id": str(user_cult["_id"]), "cult2_id": str(target["_id"])},
                {"cult1_id": str(target["_id"]), "cult2_id": str(user_cult["_id"])}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if alliance:
            await interaction.response.send_message("❌ Cannot declare war on allied cults!", ephemeral=True)
            return
        
        # Create war
        start_time = datetime.now(timezone.utc)
        end_time = start_time + duration_delta
        
        war_data = {
            "guild_id": interaction.guild.id,
            "attacker_cult_id": str(user_cult["_id"]),
            "defender_cult_id": str(target["_id"]),
            "attacker_name": user_cult["cult_name"],
            "defender_name": target["cult_name"],
            "race_type": race_type,
            "start_time": start_time,
            "end_time": end_time,
            "declared_by": interaction.user.id,
            "active": True
        }
        
        await self.bot.db.cult_wars.insert_one(war_data)
        
        # Create war announcement embed
        embed = discord.Embed(
            title="⚔️ WAR DECLARED!",
            description=f"{user_cult['cult_icon']} **{user_cult['cult_name']}** has declared war on {target['cult_icon']} **{target['cult_name']}**!",
            color=0xff0000
        )
        embed.add_field(name="War Type", value=race_type.title(), inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
        embed.add_field(name="Declared by", value=interaction.user.mention, inline=False)
        
        # Get leaders and officers to ping
        ping_users = set()
        
        # Add both cult leaders
        ping_users.add(user_cult["cult_leader_id"])
        ping_users.add(target["cult_leader_id"])
        
        # Add officers from both cults
        for cult in [user_cult, target]:
            if cult.get("officer_role_id"):
                officer_role = interaction.guild.get_role(cult["officer_role_id"])
                if officer_role:
                    for member in officer_role.members:
                        ping_users.add(member.id)
        
        # Create ping string
        ping_mentions = " ".join([f"<@{user_id}>" for user_id in ping_users])
        
        await interaction.response.send_message(f"{ping_mentions}\n", embed=embed)
        
        # Send DMs to leaders and officers
        for user_id in ping_users:
            try:
                user = interaction.guild.get_member(user_id)
                if user:
                    dm_embed = discord.Embed(
                        title="⚔️ Cult War Notification",
                        description=f"A war has been declared between {user_cult['cult_icon']} **{user_cult['cult_name']}** and {target['cult_icon']} **{target['cult_name']}**!",
                        color=0xff0000
                    )
                    dm_embed.add_field(name="War Type", value=race_type.title(), inline=True)
                    dm_embed.add_field(name="Duration", value=duration, inline=True)
                    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
                    
                    await user.send(embed=dm_embed)
            except:
                pass  # Ignore DM failures

async def setup(bot):
    await bot.add_cog(CultWar(bot))