import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.permissions import check_bot_manager

class EditCult(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cult_autocomplete(self, interaction: discord.Interaction, current: str):
        if not interaction.guild or self.bot.db is None:
            return []
        
        cults = await self.bot.db.cults.find({
            "guild_id": interaction.guild.id,
            "active": True
        }).to_list(25)
        
        return [
            app_commands.Choice(name=f"{cult['cult_icon']} {cult['cult_name']}", value=cult['cult_name'])
            for cult in cults
            if current.lower() in cult['cult_name'].lower()
        ]
    
    @app_commands.command(name="edit_cult", description="Edit cult information (Bot Manager only)")
    @app_commands.describe(
        cult_name="Select cult to edit",
        new_name="New cult name (optional)",
        new_icon="New cult emoji (optional)",
        new_description="New cult description (optional)",
        new_leader="New cult leader (optional)",
        member_role="Member role (optional)",
        leader_role="Leader role (optional)",
        officer_role="Officer role (optional)"
    )
    @app_commands.autocomplete(cult_name=cult_autocomplete)
    async def edit_cult(
        self,
        interaction: discord.Interaction,
        cult_name: str,
        new_name: str = None,
        new_icon: str = None,
        new_description: str = None,
        new_leader: discord.Member = None,
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
        
        # Find cult
        cult = await self.bot.db.cults.find_one({
            "guild_id": interaction.guild.id,
            "cult_name": cult_name,
            "active": True
        })
        
        if not cult:
            await interaction.response.send_message("❌ Cult not found!", ephemeral=True)
            return
        
        # Check if any changes provided
        if not any([new_name, new_icon, new_description, new_leader, member_role, leader_role, officer_role]):
            await interaction.response.send_message("❌ Please provide at least one field to edit!", ephemeral=True)
            return
        
        # Validation
        if new_name and len(new_name) > 50:
            await interaction.response.send_message("❌ Cult name must be 50 characters or less!", ephemeral=True)
            return
        
        if new_description and len(new_description) > 100:
            await interaction.response.send_message("❌ Cult description must be 100 characters or less!", ephemeral=True)
            return
        
        # Check for duplicates
        if new_name and new_name != cult_name:
            existing_name = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "cult_name": {"$regex": f"^{new_name}$", "$options": "i"},
                "_id": {"$ne": cult["_id"]},
                "active": True
            })
            if existing_name:
                await interaction.response.send_message("❌ A cult with this name already exists!", ephemeral=True)
                return
        
        if new_icon and new_icon != cult["cult_icon"]:
            existing_icon = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "cult_icon": new_icon,
                "_id": {"$ne": cult["_id"]},
                "active": True
            })
            if existing_icon:
                await interaction.response.send_message("❌ This emoji is already used by another cult!", ephemeral=True)
                return
        
        # Check if new leader is available
        if new_leader and new_leader.id not in cult["members"]:
            existing_member = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "members": new_leader.id,
                "active": True
            })
            if existing_member:
                await interaction.response.send_message("❌ New leader is already in another cult!", ephemeral=True)
                return
        
        # Check for role conflicts
        role_conflicts = []
        if member_role:
            existing_member_role = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "member_role_id": member_role.id,
                "_id": {"$ne": cult["_id"]},
                "active": True
            })
            if existing_member_role:
                role_conflicts.append(f"Member role {member_role.mention}")
        
        # Leader role can be shared - remove this check
        
        if officer_role:
            existing_officer_role = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "officer_role_id": officer_role.id,
                "_id": {"$ne": cult["_id"]},
                "active": True
            })
            if existing_officer_role:
                role_conflicts.append(f"Officer role {officer_role.mention}")
        
        if role_conflicts:
            await interaction.response.send_message(f"❌ These roles are already used by other cults: {', '.join(role_conflicts)}", ephemeral=True)
            return
        
        # Build update data
        update_data = {"edited_at": datetime.now(timezone.utc)}
        changes = []
        
        if new_name:
            update_data["cult_name"] = new_name
            changes.append(f"**Name:** {cult['cult_name']} → {new_name}")
        
        if new_icon:
            update_data["cult_icon"] = new_icon
            changes.append(f"**Icon:** {cult['cult_icon']} → {new_icon}")
        
        if new_description:
            update_data["cult_description"] = new_description
            changes.append(f"**Description:** {cult['cult_description']} → {new_description}")
        
        if new_leader:
            old_leader_id = cult["cult_leader_id"]
            update_data["cult_leader_id"] = new_leader.id
            
            # Add new leader to members if not already
            if new_leader.id not in cult["members"]:
                await self.bot.db.cults.update_one(
                    {"_id": cult["_id"]},
                    {"$push": {"members": new_leader.id}}
                )
            
            changes.append(f"**Leader:** <@{old_leader_id}> → {new_leader.mention}")
        
        if member_role is not None:
            update_data["member_role_id"] = member_role.id if member_role else None
            changes.append(f"**Member Role:** {member_role.mention if member_role else 'None'}")
        
        if leader_role is not None:
            update_data["leader_role_id"] = leader_role.id if leader_role else None
            changes.append(f"**Leader Role:** {leader_role.mention if leader_role else 'None'}")
        
        if officer_role is not None:
            update_data["officer_role_id"] = officer_role.id if officer_role else None
            changes.append(f"**Officer Role:** {officer_role.mention if officer_role else 'None'}")
        
        # Update cult
        await self.bot.db.cults.update_one(
            {"_id": cult["_id"]},
            {"$set": update_data}
        )
        
        # Handle role changes
        try:
            if new_leader:
                old_leader = interaction.guild.get_member(old_leader_id)
                if old_leader and leader_role:
                    await old_leader.remove_roles(leader_role, reason="Leadership transferred")
                if leader_role:
                    await new_leader.add_roles(leader_role, reason=f"New leader of cult: {new_name or cult_name}")
        except discord.Forbidden:
            pass
        
        # Create embed
        embed = discord.Embed(
            title=f"✏️ Cult Updated",
            description="\n".join(changes),
            color=0xffa500
        )
        embed.set_footer(text=f"Updated by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EditCult(bot))