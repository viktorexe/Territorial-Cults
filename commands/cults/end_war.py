import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

class EndWar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="end_war", description="End your cult's ongoing war (Leaders/Officers only)")
    async def end_war(self, interaction: discord.Interaction):
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
            await interaction.response.send_message("❌ You must be in a cult to end a war!", ephemeral=True)
            return
        
        # Check if user is leader or officer
        is_leader = user_cult["cult_leader_id"] == interaction.user.id
        is_officer = False
        
        if user_cult.get("officer_role_id"):
            officer_role = interaction.guild.get_role(user_cult["officer_role_id"])
            is_officer = officer_role and officer_role in interaction.user.roles
        
        if not (is_leader or is_officer):
            await interaction.response.send_message("❌ Only cult leaders and officers can end wars!", ephemeral=True)
            return
        
        # Find active war where this cult is the attacker (only attacker can end war)
        war = await self.bot.db.cult_wars.find_one({
            "attacker_cult_id": str(user_cult["_id"]),
            "guild_id": interaction.guild.id,
            "active": True
        })
        
        if not war:
            await interaction.response.send_message("❌ Your cult has no active war to end, or you didn't start the war!", ephemeral=True)
            return
        
        # Get defender cult info
        from bson import ObjectId
        defender_cult = await self.bot.db.cults.find_one({"_id": ObjectId(war["defender_cult_id"])})
        
        # End the war
        await self.bot.db.cult_wars.update_one(
            {"_id": war["_id"]},
            {
                "$set": {
                    "active": False,
                    "ended_by": interaction.user.id,
                    "ended_at": datetime.now(timezone.utc)
                }
            }
        )
        
        # Create announcement embed
        embed = discord.Embed(
            title="🏳️ WAR ENDED",
            description=f"The war between {user_cult['cult_icon']} **{user_cult['cult_name']}** and {defender_cult['cult_icon']} **{defender_cult['cult_name']}** has ended!",
            color=0x808080
        )
        embed.add_field(name="War Type", value=war["race_type"].title(), inline=True)
        embed.add_field(name="Duration", value=f"<t:{int(war['start_time'].timestamp())}:R> - <t:{int(datetime.now(timezone.utc).timestamp())}:R>", inline=True)
        embed.add_field(name="Ended by", value=interaction.user.mention, inline=False)
        
        # Get leaders and officers to notify
        ping_users = set()
        
        # Add both cult leaders
        ping_users.add(user_cult["cult_leader_id"])
        ping_users.add(defender_cult["cult_leader_id"])
        
        # Add officers from both cults
        for cult in [user_cult, defender_cult]:
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
                        title="🏳️ War Ended Notification",
                        description=f"The war between {user_cult['cult_icon']} **{user_cult['cult_name']}** and {defender_cult['cult_icon']} **{defender_cult['cult_name']}** has ended!",
                        color=0x808080
                    )
                    dm_embed.add_field(name="Ended by", value=interaction.user.display_name, inline=True)
                    dm_embed.add_field(name="Server", value=interaction.guild.name, inline=True)
                    
                    await user.send(embed=dm_embed)
            except:
                pass  # Ignore DM failures

async def setup(bot):
    await bot.add_cog(EndWar(bot))