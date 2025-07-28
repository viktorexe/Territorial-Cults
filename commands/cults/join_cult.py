import discord
from discord.ext import commands
from discord import app_commands

class JoinCult(commands.Cog):
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
    
    @app_commands.command(name="join_cult", description="Join a cult")
    @app_commands.describe(cult_name="Select a cult to join")
    @app_commands.autocomplete(cult_name=cult_autocomplete)
    async def join_cult(self, interaction: discord.Interaction, cult_name: str):
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        guild_id = interaction.guild.id
        
        # Check if user is already in a cult
        existing_cult = await self.bot.db.cults.find_one({
            "guild_id": guild_id,
            "members": user_id,
            "active": True
        })
        if existing_cult:
            await interaction.response.send_message(f"❌ You are already in {existing_cult['cult_icon']} {existing_cult['cult_name']}!", ephemeral=True)
            return
        
        # Find the cult
        cult = await self.bot.db.cults.find_one({
            "guild_id": guild_id,
            "cult_name": cult_name,
            "active": True
        })
        
        if not cult:
            await interaction.response.send_message("❌ Cult not found!", ephemeral=True)
            return
        
        # Add user to cult
        await self.bot.db.cults.update_one(
            {"_id": cult["_id"]},
            {"$push": {"members": user_id}}
        )
        
        # Assign member role
        try:
            if cult.get("member_role_id"):
                member_role = interaction.guild.get_role(cult["member_role_id"])
                if member_role:
                    await interaction.user.add_roles(member_role, reason=f"Joined cult: {cult['cult_name']}")
        except discord.Forbidden:
            pass
        
        # Create embed
        embed = discord.Embed(
            title="✅ Joined Cult",
            description=f"You successfully joined {cult['cult_icon']} {cult['cult_name']}!",
            color=0x00ff00
        )
        embed.add_field(name="Leader", value=f"<@{cult['cult_leader_id']}>", inline=True)
        embed.add_field(name="Description", value=cult['cult_description'], inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(JoinCult(bot))