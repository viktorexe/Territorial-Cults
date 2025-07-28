import discord
from discord.ext import commands
from discord import app_commands

class PromoteMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="promote_member", description="Promote a cult member to officer (Leaders only)")
    @app_commands.describe(member="Member to promote to officer")
    async def promote_member(self, interaction: discord.Interaction, member: discord.Member):
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
            await interaction.response.send_message("❌ You must be a cult leader to promote members!", ephemeral=True)
            return
        
        # Check if member is in the same cult
        if member.id not in user_cult["members"]:
            await interaction.response.send_message("❌ This user is not in your cult!", ephemeral=True)
            return
        
        # Check if member is the leader
        if member.id == user_cult["cult_leader_id"]:
            await interaction.response.send_message("❌ Cannot promote the cult leader!", ephemeral=True)
            return
        
        # Check if cult has officer role configured
        if not user_cult.get("officer_role_id"):
            await interaction.response.send_message("❌ This cult doesn't have an officer role configured!", ephemeral=True)
            return
        
        officer_role = interaction.guild.get_role(user_cult["officer_role_id"])
        if not officer_role:
            await interaction.response.send_message("❌ Officer role not found!", ephemeral=True)
            return
        
        # Check if member already has officer role
        if officer_role in member.roles:
            await interaction.response.send_message("❌ This member is already an officer!", ephemeral=True)
            return
        
        # Promote member
        try:
            await member.add_roles(officer_role, reason=f"Promoted to officer in cult: {user_cult['cult_name']}")
            
            embed = discord.Embed(
                title="📈 Member Promoted",
                description=f"{member.mention} has been promoted to officer in {user_cult['cult_icon']} {user_cult['cult_name']}!",
                color=0x00ff00
            )
            embed.add_field(name="Promoted by", value=interaction.user.mention, inline=True)
            embed.add_field(name="New Role", value=officer_role.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to assign this role!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PromoteMember(bot))