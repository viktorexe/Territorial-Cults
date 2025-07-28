import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class AllianceView(discord.ui.View):
    def __init__(self, proposer_cult, target_cult, guild_id):
        super().__init__(timeout=300)
        self.proposer_cult = proposer_cult
        self.target_cult = target_cult
        self.guild_id = guild_id
    
    @discord.ui.button(label="Accept Alliance", style=discord.ButtonStyle.success, emoji="🤝")
    async def accept_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user is leader or officer of target cult
        is_leader = self.target_cult["cult_leader_id"] == interaction.user.id
        is_officer = False
        
        if self.target_cult.get("officer_role_id"):
            officer_role = interaction.guild.get_role(self.target_cult["officer_role_id"])
            is_officer = officer_role and officer_role in interaction.user.roles
        
        if not (is_leader or is_officer):
            await interaction.response.send_message("❌ Only the target cult's leader or officers can accept this alliance!", ephemeral=True)
            return
        
        # Create alliance record
        alliance_data = {
            "guild_id": self.guild_id,
            "cult1_id": str(self.proposer_cult["_id"]),
            "cult2_id": str(self.target_cult["_id"]),
            "cult1_name": self.proposer_cult["cult_name"],
            "cult2_name": self.target_cult["cult_name"],
            "created_at": datetime.now(timezone.utc),
            "accepted_by": interaction.user.id,
            "active": True
        }
        
        bot = interaction.client
        await bot.db.cult_alliances.insert_one(alliance_data)
        
        # Update embed
        embed = discord.Embed(
            title="🤝 Alliance Formed!",
            description=f"{self.proposer_cult['cult_icon']} **{self.proposer_cult['cult_name']}** and {self.target_cult['cult_icon']} **{self.target_cult['cult_name']}** are now allied!",
            color=0x00ff00
        )
        embed.add_field(name="Accepted by", value=interaction.user.mention, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="Decline Alliance", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline_alliance(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user is leader or officer of target cult
        is_leader = self.target_cult["cult_leader_id"] == interaction.user.id
        is_officer = False
        
        if self.target_cult.get("officer_role_id"):
            officer_role = interaction.guild.get_role(self.target_cult["officer_role_id"])
            is_officer = officer_role and officer_role in interaction.user.roles
        
        if not (is_leader or is_officer):
            await interaction.response.send_message("❌ Only the target cult's leader or officers can decline this alliance!", ephemeral=True)
            return
        
        # Update embed
        embed = discord.Embed(
            title="❌ Alliance Declined",
            description=f"{self.target_cult['cult_icon']} **{self.target_cult['cult_name']}** has declined the alliance with {self.proposer_cult['cult_icon']} **{self.proposer_cult['cult_name']}**.",
            color=0xff0000
        )
        embed.add_field(name="Declined by", value=interaction.user.mention, inline=True)
        
        await interaction.response.edit_message(embed=embed, view=None)

class CultAlliance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cult_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.guild or self.bot.db is None:
            return []
        
        # Get user's cult to exclude it
        user_cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_leader_id": interaction.user.id,
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
    
    @app_commands.command(name="cult_alliance", description="Propose alliance with another cult (Leaders only)")
    @app_commands.describe(target_cult="Cult to propose alliance with")
    @app_commands.autocomplete(target_cult=cult_autocomplete)
    async def cult_alliance(self, interaction: discord.Interaction, target_cult: str):
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
            await interaction.response.send_message("❌ You must be a cult leader to propose alliances!", ephemeral=True)
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
        
        # Check for existing alliance
        existing_alliance = await self.bot.db.cult_alliances.find_one({
            "$or": [
                {"cult1_id": str(user_cult["_id"]), "cult2_id": str(target["_id"])},
                {"cult1_id": str(target["_id"]), "cult2_id": str(user_cult["_id"])}
            ],
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if existing_alliance:
            await interaction.response.send_message("❌ Alliance already exists between these cults!", ephemeral=True)
            return
        
        # Create proposal embed
        embed = discord.Embed(
            title="🤝 Alliance Proposal",
            description=f"{user_cult['cult_icon']} **{user_cult['cult_name']}** proposes an alliance with {target['cult_icon']} **{target['cult_name']}**!",
            color=0x0099ff
        )
        embed.add_field(name="Proposed by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Benefits", value="• Cannot declare war on each other\n• Diplomatic cooperation", inline=False)
        
        # Get target cult leader and officers to ping
        ping_users = {target["cult_leader_id"]}
        if target.get("officer_role_id"):
            officer_role = interaction.guild.get_role(target["officer_role_id"])
            if officer_role:
                for member in officer_role.members:
                    ping_users.add(member.id)
        
        ping_mentions = " ".join([f"<@{user_id}>" for user_id in ping_users])
        
        view = AllianceView(user_cult, target, interaction.guild.id)
        
        await interaction.response.send_message(f"{ping_mentions}\n", embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CultAlliance(bot))