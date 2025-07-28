import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class CultCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="cult_create", description="Create a new cult (Bot Manager only)")
    @app_commands.describe(
        cult_leader="User to be the cult leader",
        cult_name="Name of the cult",
        cult_icon="Emoji icon for the cult",
        cult_description="Description of the cult",
        member_role="Role for cult members (optional)",
        leader_role="Role for cult leader (optional)",
        officer_role="Role for cult officers (optional)"
    )
    async def cult_create(
        self, 
        interaction: discord.Interaction, 
        cult_leader: discord.Member,
        cult_name: str,
        cult_icon: str,
        cult_description: str,
        member_role: discord.Role = None,
        leader_role: discord.Role = None,
        officer_role: discord.Role = None
    ):
        # Permission check
        if not await check_bot_manager(self.bot, interaction):
            await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
            return
        
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        # Validation
        if len(cult_name) > 50:
            await interaction.response.send_message("❌ Cult name must be 50 characters or less!", ephemeral=True)
            return
        
        if len(cult_description) > 100:
            await interaction.response.send_message("❌ Cult description must be 100 characters or less!", ephemeral=True)
            return
        
        # Check for duplicates
        existing_name = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_name": {"$regex": f"^{cult_name}$", "$options": "i"},
            "active": True
        })
        if existing_name:
            await interaction.response.send_message("❌ A cult with this name already exists!", ephemeral=True)
            return
        
        existing_icon = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_icon": cult_icon,
            "active": True
        })
        if existing_icon:
            await interaction.response.send_message("❌ This emoji is already used by another cult!", ephemeral=True)
            return
        
        # Check for role conflicts
        role_conflicts = []
        if member_role:
            existing_member_role = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "member_role_id": member_role.id,
                "active": True
            })
            if existing_member_role:
                role_conflicts.append(f"Member role {member_role.mention}")
        
        # Leader role can be shared - remove this check
        
        if officer_role:
            existing_officer_role = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "officer_role_id": officer_role.id,
                "active": True
            })
            if existing_officer_role:
                role_conflicts.append(f"Officer role {officer_role.mention}")
        
        if role_conflicts:
            await interaction.response.send_message(f"❌ These roles are already used by other cults: {', '.join(role_conflicts)}", ephemeral=True)
            return
        
        # Check if leader is already in a cult
        existing_leader = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "members": cult_leader.id,
            "active": True
        })
        if existing_leader:
            await interaction.response.send_message("❌ This user is already in another cult!", ephemeral=True)
            return
        
        # Create cult
        cult_data = {
            "guild_id": interaction.guild.id,
            "cult_name": cult_name,
            "cult_icon": cult_icon,
            "cult_description": cult_description,
            "cult_leader_id": cult_leader.id,
            "members": [cult_leader.id],
            "member_role_id": member_role.id if member_role else None,
            "leader_role_id": leader_role.id if leader_role else None,
            "officer_role_id": officer_role.id if officer_role else None,
            "created_by": interaction.user.id,
            "created_at": datetime.now(timezone.utc),
            "active": True
        }
        
        result = await self.bot.db.cults.insert_one(cult_data)
        
        # Assign roles
        try:
            if member_role:
                await cult_leader.add_roles(member_role, reason=f"Joined cult: {cult_name}")
            if leader_role:
                await cult_leader.add_roles(leader_role, reason=f"Leader of cult: {cult_name}")
        except discord.Forbidden:
            pass
        
        # Create embed
        embed = discord.Embed(
            title=f"{cult_icon} Cult Created",
            description=f"**{cult_name}** has been established!",
            color=0x00ff00
        )
        embed.add_field(name="Leader", value=cult_leader.mention, inline=True)
        embed.add_field(name="Description", value=cult_description, inline=False)
        
        if member_role:
            embed.add_field(name="Member Role", value=member_role.mention, inline=True)
        if leader_role:
            embed.add_field(name="Leader Role", value=leader_role.mention, inline=True)
        if officer_role:
            embed.add_field(name="Officer Role", value=officer_role.mention, inline=True)
        
        embed.set_footer(text=f"Created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CultCreate(bot))