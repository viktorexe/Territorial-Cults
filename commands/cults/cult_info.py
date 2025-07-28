import discord
from discord.ext import commands
from discord import app_commands

class CultInfo(commands.Cog):
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
    
    @app_commands.command(name="cult_info", description="Show detailed information about a cult")
    @app_commands.describe(cult_name="Select cult to view information")
    @app_commands.autocomplete(cult_name=cult_autocomplete)
    async def cult_info(self, interaction: discord.Interaction, cult_name: str):
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
        
        # Get leader info
        leader = interaction.guild.get_member(cult["cult_leader_id"])
        leader_text = leader.mention if leader else "Unknown"
        
        # Get member list
        members = []
        officers = []
        
        for member_id in cult["members"]:
            member = interaction.guild.get_member(member_id)
            if not member:
                continue
            
            # Check if member has officer role
            if cult.get("officer_role_id"):
                officer_role = interaction.guild.get_role(cult["officer_role_id"])
                if officer_role and officer_role in member.roles:
                    officers.append(member.mention)
                    continue
            
            # Skip leader from regular members
            if member_id != cult["cult_leader_id"]:
                members.append(member.mention)
        
        # Create embed
        embed = discord.Embed(
            title=f"{cult['cult_icon']} {cult['cult_name']}",
            description=cult['cult_description'],
            color=0x00ff00
        )
        
        # Basic info
        embed.add_field(name="Leader", value=leader_text, inline=True)
        embed.add_field(name="Total Members", value=str(len(cult['members'])), inline=True)
        embed.add_field(name="Created", value=f"<t:{int(cult['created_at'].timestamp())}:R>", inline=True)
        
        # Officers
        if officers:
            embed.add_field(name=f"Officers ({len(officers)})", value="\n".join(officers[:10]), inline=False)
        
        # Members
        if members:
            member_text = "\n".join(members[:15])
            if len(members) > 15:
                member_text += f"\n... and {len(members) - 15} more"
            embed.add_field(name=f"Members ({len(members)})", value=member_text, inline=False)
        
        # Roles info
        role_info = []
        if cult.get("member_role_id"):
            member_role = interaction.guild.get_role(cult["member_role_id"])
            if member_role:
                role_info.append(f"Member: {member_role.mention}")
        
        if cult.get("leader_role_id"):
            leader_role = interaction.guild.get_role(cult["leader_role_id"])
            if leader_role:
                role_info.append(f"Leader: {leader_role.mention}")
        
        if cult.get("officer_role_id"):
            officer_role = interaction.guild.get_role(cult["officer_role_id"])
            if officer_role:
                role_info.append(f"Officer: {officer_role.mention}")
        
        if role_info:
            embed.add_field(name="Roles", value="\n".join(role_info), inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CultInfo(bot))