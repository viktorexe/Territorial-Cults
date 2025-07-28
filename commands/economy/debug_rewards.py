import discord
from discord.ext import commands
from discord import app_commands

class DebugRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="debug_rewards", description="Debug reward system (Admin only)")
    async def debug_rewards(self, interaction: discord.Interaction):
        try:
            if not (interaction.user.id == 780678948949721119 or interaction.user.guild_permissions.administrator):
                await interaction.response.send_message("❌ Administrator permission required!", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            guild_id = interaction.guild.id
            user_id = interaction.user.id
            
            # Get reward roles for this guild
            rewards = await self.bot.db.reward_roles.find({
                "guild_id": guild_id,
                "active": True
            }).to_list(None)
            
            if not rewards:
                await interaction.followup.send("❌ No reward roles found!")
                return
            
            results = []
            
            for reward in rewards[:8]:  # Limit to 8 rewards
                role = interaction.guild.get_role(reward["role_id"])
                if not role:
                    results.append(f"❌ {reward['role_name']} not found")
                    continue
                
                # Check user's points/wins
                collection = self.bot.db.points if reward["type"] == "points" else self.bot.db.wins
                
                user_total = await collection.aggregate([
                    {"$match": {"guild_id": guild_id, "user_id": user_id}},
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                ]).to_list(1)
                
                total = user_total[0]["total"] if user_total else 0
                has_role = role in interaction.user.roles
                eligible = total >= reward["amount"]
                
                results.append(f"**{role.name}** ({reward['amount']} {reward['type']})")
                results.append(f"Total: {total} | {'✅' if eligible else '❌'} | {'Has' if has_role else 'Missing'}")
                results.append("")
            
            if len(rewards) > 8:
                results.append(f"... and {len(rewards) - 8} more")
            
            description = "\n".join(results)
            if len(description) > 4000:
                description = description[:4000] + "..."
            
            embed = discord.Embed(
                title="🔍 Reward Debug Info",
                description=description,
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Debug error: {e}")
            print(f"Debug rewards error: {e}")

async def setup(bot):
    await bot.add_cog(DebugRewards(bot))