import discord
from discord.ext import commands
from discord import app_commands
from datetime import timezone
import logging
import traceback

class CultStats(commands.Cog):
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
    
    @app_commands.command(name="cult_stats", description="Show detailed stats for a cult")
    @app_commands.describe(cult_name="Select a cult to view stats")
    @app_commands.autocomplete(cult_name=cult_autocomplete)
    async def cult_stats(self, interaction: discord.Interaction, cult_name: str):
        try:
            # Initial response to prevent timeout
            await interaction.response.defer()
            
            if self.bot.db is None:
                await interaction.followup.send("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.followup.send("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            # Find cult
            cult = await self.bot.db.cults.find_one({
                "guild_id": interaction.guild.id,
                "cult_name": cult_name,
                "active": True
            })
            
            if not cult:
                await interaction.followup.send("❌ Cult not found!", ephemeral=True)
                return
                
            # Safety check for members list
            if not cult.get("members") or not isinstance(cult["members"], list):
                await interaction.followup.send("❌ Invalid cult data: missing members list!", ephemeral=True)
                return
            
            # Calculate total points and wins since each member joined
            total_points = 0
            total_wins = 0
            member_stats = []
            
            for member_id in cult["members"]:
                try:
                    # Find earliest record where user was in this cult
                    earliest_cult_record = await self.bot.db.points.find_one({
                        "guild_id": interaction.guild.id,
                        "user_id": member_id,
                        "cult_id": str(cult["_id"])
                    }, sort=[("timestamp", 1)])
                    
                    if earliest_cult_record and "timestamp" in earliest_cult_record:
                        member_join_date = earliest_cult_record["timestamp"]
                    else:
                        # Check wins collection too
                        earliest_wins_record = await self.bot.db.wins.find_one({
                            "guild_id": interaction.guild.id,
                            "user_id": member_id,
                            "cult_id": str(cult["_id"])
                        }, sort=[("timestamp", 1)])
                        
                        if earliest_wins_record and "timestamp" in earliest_wins_record:
                            member_join_date = earliest_wins_record["timestamp"]
                        else:
                            # Fallback to cult creation date
                            member_join_date = cult.get("created_at")
                            if not member_join_date:
                                # Skip this member if no valid date found
                                continue
                    
                    if member_join_date.tzinfo is None:
                        member_join_date = member_join_date.replace(tzinfo=timezone.utc)
                    
                    # Points since member joined cult (only records with this cult_id)
                    points_result = await self.bot.db.points.aggregate([
                        {"$match": {
                            "guild_id": interaction.guild.id,
                            "user_id": member_id,
                            "cult_id": str(cult["_id"]),
                            "timestamp": {"$gte": member_join_date}
                        }},
                        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                    ]).to_list(1)
                    
                    member_points = points_result[0]["total"] if points_result and points_result[0].get("total") else 0
                    total_points += member_points
                    
                    # Wins since member joined cult (only records with this cult_id)
                    wins_result = await self.bot.db.wins.aggregate([
                        {"$match": {
                            "guild_id": interaction.guild.id,
                            "user_id": member_id,
                            "cult_id": str(cult["_id"]),
                            "timestamp": {"$gte": member_join_date}
                        }},
                        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                    ]).to_list(1)
                    
                    member_wins = wins_result[0]["total"] if wins_result and wins_result[0].get("total") else 0
                    total_wins += member_wins
                    
                    member_stats.append({
                        "user_id": member_id,
                        "points": member_points,
                        "wins": member_wins
                    })
                except Exception as e:
                    logging.error(f"Error processing member {member_id} in cult_stats: {e}")
                    # Continue with next member instead of crashing
                    continue
            
            # Sort members by points
            member_stats.sort(key=lambda x: x["points"], reverse=True)
            
            # Create embed
            embed = discord.Embed(
                title=f"{cult.get('cult_icon', '🏆')} {cult.get('cult_name', 'Cult')}",
                description=cult.get('cult_description', 'No description'),
                color=0x00ff00
            )
            
            # Basic info
            leader_id = cult.get("cult_leader_id")
            leader = interaction.guild.get_member(leader_id) if leader_id else None
            leader_name = leader.mention if leader else "Unknown"
            
            embed.add_field(name="Leader", value=leader_name, inline=True)
            embed.add_field(name="Members", value=str(len(cult['members'])), inline=True)
            
            # Safely handle created_at timestamp
            created_at = cult.get("created_at")
            if created_at:
                try:
                    embed.add_field(name="Created", value=f"<t:{int(created_at.timestamp())}:R>", inline=True)
                except (AttributeError, TypeError):
                    embed.add_field(name="Created", value="Unknown", inline=True)
            else:
                embed.add_field(name="Created", value="Unknown", inline=True)
            
            embed.add_field(name="Total Points", value=f"{total_points:,.0f}", inline=True)
            embed.add_field(name="Total Wins", value=f"{total_wins:,.0f}", inline=True)
            
            # Safely calculate average points
            member_count = len(cult['members'])
            if member_count > 0:
                avg_points = total_points / member_count
                embed.add_field(name="Avg Points/Member", value=f"{avg_points:,.0f}", inline=True)
            else:
                embed.add_field(name="Avg Points/Member", value="0", inline=True)
            
            # Top 5 members
            if member_stats:
                top_members = ""
                for i, member in enumerate(member_stats[:5], 1):
                    top_members += f"{i}. <@{member['user_id']}> - {member['points']:,.0f} pts, {member['wins']:,.0f} wins\n"
                
                embed.add_field(name="Top Members", value=top_members, inline=False)
            
            try:
                # War history
                wars_won = await self.bot.db.cult_wars.count_documents({
                    "winner_cult_id": str(cult["_id"]),
                    "active": False
                })
                
                wars_lost = await self.bot.db.cult_wars.count_documents({
                    "$or": [
                        {"attacker_cult_id": str(cult["_id"])},
                        {"defender_cult_id": str(cult["_id"])}
                    ],
                    "winner_cult_id": {"$ne": str(cult["_id"])},
                    "winner_cult_id": {"$ne": None},
                    "active": False
                })
                
                wars_tied = await self.bot.db.cult_wars.count_documents({
                    "$or": [
                        {"attacker_cult_id": str(cult["_id"])},
                        {"defender_cult_id": str(cult["_id"])}
                    ],
                    "winner_cult_id": None,
                    "active": False
                })
                
                if wars_won > 0 or wars_lost > 0 or wars_tied > 0:
                    embed.add_field(name="War Record", value=f"Won: {wars_won} | Lost: {wars_lost} | Tied: {wars_tied}", inline=False)
            except Exception as e:
                logging.error(f"Error getting war history in cult_stats: {e}")
                # Continue without war history instead of crashing
            
            try:
                # Alliance info
                alliances = await self.bot.db.cult_alliances.find({
                    "$or": [
                        {"cult1_id": str(cult["_id"])},
                        {"cult2_id": str(cult["_id"])}
                    ],
                    "guild_id": interaction.guild.id,
                    "active": True
                }).to_list(None)
                
                if alliances:
                    alliance_names = []
                    for alliance in alliances:
                        if alliance.get("cult1_id") == str(cult["_id"]):
                            alliance_names.append(alliance.get("cult2_name", "Unknown"))
                        else:
                            alliance_names.append(alliance.get("cult1_name", "Unknown"))
                    
                    if alliance_names:
                        embed.add_field(name="Alliances", value="\n".join(alliance_names[:5]), inline=False)
            except Exception as e:
                logging.error(f"Error getting alliance info in cult_stats: {e}")
                # Continue without alliance info instead of crashing
            
            await interaction.followup.send(embed=embed)
                
        except Exception as e:
            error_msg = f"An error occurred in cult_stats: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ An error occurred while fetching cult stats!", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ An error occurred while fetching cult stats!", ephemeral=True)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(CultStats(bot))