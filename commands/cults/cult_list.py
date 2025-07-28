import discord
from discord.ext import commands
from discord import app_commands

class CultJoinView(discord.ui.View):
    def __init__(self, bot, cults):
        super().__init__(timeout=None)
        self.bot = bot
        
        # Add join buttons for each cult
        for cult in cults:
            button = discord.ui.Button(
                label=cult['cult_name'],
                emoji=cult['cult_icon'],
                style=discord.ButtonStyle.secondary,
                custom_id=f"join_cult_{cult['_id']}"
            )
            button.callback = self.join_cult_callback
            self.add_item(button)
        
        # Add leave cult button
        leave_button = discord.ui.Button(
            label="Leave Cult",
            style=discord.ButtonStyle.danger,
            custom_id="leave_cult"
        )
        leave_button.callback = self.leave_cult_callback
        self.add_item(leave_button)
    
    async def join_cult_callback(self, interaction: discord.Interaction):
        try:
            cult_id = interaction.data['custom_id'].replace('join_cult_', '')
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
            
            # Get cult data
            from bson import ObjectId
            cult = await self.bot.db.cults.find_one({"_id": ObjectId(cult_id)})
            if not cult:
                await interaction.response.send_message("❌ Cult not found!", ephemeral=True)
                return
            
            # Add user to cult
            await self.bot.db.cults.update_one(
                {"_id": ObjectId(cult_id)},
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
            
            await interaction.response.send_message(f"✅ You joined {cult['cult_icon']} {cult['cult_name']}!", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error joining cult!", ephemeral=True)
    
    async def leave_cult_callback(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            guild_id = interaction.guild.id
            
            # Find user's cult
            cult = await self.bot.db.cults.find_one({
                "guild_id": guild_id,
                "members": user_id,
                "active": True
            })
            
            if not cult:
                await interaction.response.send_message("❌ You are not in any cult!", ephemeral=True)
                return
            
            # Check if user is cult leader
            if cult['cult_leader_id'] == user_id:
                await interaction.response.send_message("❌ Cult leaders cannot leave their cult!", ephemeral=True)
                return
            
            # Remove user from cult
            await self.bot.db.cults.update_one(
                {"_id": cult['_id']},
                {"$pull": {"members": user_id}}
            )
            
            # Remove member role
            try:
                if cult.get("member_role_id"):
                    member_role = interaction.guild.get_role(cult["member_role_id"])
                    if member_role and member_role in interaction.user.roles:
                        await interaction.user.remove_roles(member_role, reason=f"Left cult: {cult['cult_name']}")
            except discord.Forbidden:
                pass
            
            await interaction.response.send_message(f"✅ You left {cult['cult_icon']} {cult['cult_name']}!", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message("❌ Error leaving cult!", ephemeral=True)

class CultList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="cult_list", description="List all cults in this server")
    async def cult_list(self, interaction: discord.Interaction):
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        # Get all active cults
        cults = await self.bot.db.cults.find({
            "guild_id": interaction.guild.id,
            "active": True
        }).to_list(None)
        
        if not cults:
            embed = discord.Embed(
                title=f"Showing cult list for {interaction.guild.name}",
                description="No cults found in this server.",
                color=0x2b2d31
            )
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            await interaction.response.send_message(embed=embed)
            return
        
        # Create embed
        embed = discord.Embed(
            title=f"Showing cult list for {interaction.guild.name}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        description = ""
        for i, cult in enumerate(cults, 1):
            leader = interaction.guild.get_member(cult["cult_leader_id"])
            leader_mention = leader.mention if leader else "Unknown"
            description += f"{i}. {cult['cult_icon']} {cult['cult_name']} - leader {leader_mention}\n"
        
        embed.description = description
        
        # Create view with buttons
        view = CultJoinView(self.bot, cults)
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(CultList(bot))