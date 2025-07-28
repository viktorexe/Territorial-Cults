import discord
from discord.ext import commands
from discord import app_commands

class CleanupRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="cleanup_roles", description="Remove duplicate milestone roles, keep only highest (Admin only)")
    async def cleanup_roles(self, interaction: discord.Interaction):
        try:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Administrator permission required!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            guild_id = interaction.guild.id
            
            # Get all reward roles for this guild
            rewards = await self.bot.db.reward_roles.find({
                "guild_id": guild_id,
                "active": True
            }).sort("amount", -1).to_list(None)
            
            if not rewards:
                await interaction.followup.send("❌ No reward roles found!")
                return
            
            # Group by type
            points_rewards = [r for r in rewards if r["type"] == "points"]
            wins_rewards = [r for r in rewards if r["type"] == "wins"]
            
            cleaned_users = 0
            
            for member in interaction.guild.members:
                if member.bot:
                    continue
                
                # Check points roles
                if len(points_rewards) > 1:
                    user_points_roles = []
                    for reward in points_rewards:
                        role = interaction.guild.get_role(reward["role_id"])
                        if role and role in member.roles:
                            user_points_roles.append((reward, role))
                    
                    if len(user_points_roles) > 1:
                        # Keep highest, remove others
                        highest = max(user_points_roles, key=lambda x: x[0]["amount"])
                        to_remove = [role for reward, role in user_points_roles if reward["amount"] < highest[0]["amount"]]
                        
                        if to_remove:
                            await member.remove_roles(*to_remove, reason="Cleanup: Keep only highest milestone role")
                            cleaned_users += 1
                
                # Check wins roles
                if len(wins_rewards) > 1:
                    user_wins_roles = []
                    for reward in wins_rewards:
                        role = interaction.guild.get_role(reward["role_id"])
                        if role and role in member.roles:
                            user_wins_roles.append((reward, role))
                    
                    if len(user_wins_roles) > 1:
                        # Keep highest, remove others
                        highest = max(user_wins_roles, key=lambda x: x[0]["amount"])
                        to_remove = [role for reward, role in user_wins_roles if reward["amount"] < highest[0]["amount"]]
                        
                        if to_remove:
                            await member.remove_roles(*to_remove, reason="Cleanup: Keep only highest milestone role")
                            cleaned_users += 1
            
            embed = discord.Embed(
                title="✅ Role Cleanup Complete",
                description=f"Cleaned up milestone roles for {cleaned_users} users.\nEach user now has only their highest points role and highest wins role.",
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Cleanup error: {e}")
            except:
                pass
            print(f"Cleanup roles error: {e}")

async def setup(bot):
    await bot.add_cog(CleanupRoles(bot))