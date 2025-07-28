import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger('TerritorialBot')

class AdminPoints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="adminpoints", description="Add points from leaderboard message")
    @app_commands.describe(message_id="Message ID of the leaderboard")
    async def adminpoints(self, interaction: discord.Interaction, message_id: str):
        # Permission check
        if interaction.user.id != 780678948949721119:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        # Database check
        if self.bot.db is None:
            await interaction.response.send_message("❌ Database not available!", ephemeral=True)
            return
        
        # Guild check
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
            return
        
        # Defer response
        await interaction.response.defer(ephemeral=True)
        
        # Validate message ID
        try:
            message_id_int = int(message_id)
        except ValueError:
            await interaction.followup.send("❌ Invalid message ID format!", ephemeral=True)
            return
        
        # Find message in all channels
        message = None
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id_int)
                if message:
                    break
            except discord.NotFound:
                continue
            except discord.Forbidden:
                continue
            except Exception as e:
                logger.error(f"Error fetching message from {channel.name}: {e}")
                continue
        
        if not message:
            await interaction.followup.send("❌ Message not found in any channel!", ephemeral=True)
            return
        
        try:
            guild_id = interaction.guild.id
            processed = 0
            failed = 0
            success_details = []
            
            # Check if message has embeds
            if message.embeds:
                # Process embed content
                embed = message.embeds[0]
                if embed.description:
                    content = embed.description
                else:
                    content = message.content
            else:
                content = message.content
            
            if not content:
                await interaction.followup.send("❌ Message has no content to process!", ephemeral=True)
                return
            
            logger.info(f"Processing content: {content[:200]}...")
            
            # Parse leaderboard entries
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Leaderboard') or line.startswith('Showing') or line == '⠀':
                    continue
                
                logger.info(f"Processing line: {line}")
                
                # Try multiple parsing patterns
                user = None
                points = None
                
                # Pattern 1: @username • points
                if '•' in line:
                    parts = line.split('•')
                    if len(parts) >= 2:
                        username_part = parts[0].strip()
                        points_part = parts[1].strip()
                        
                        # Extract username
                        if username_part.startswith('@'):
                            username = username_part[1:].strip()
                        else:
                            username = username_part.strip()
                        
                        # Extract points
                        try:
                            points = float(points_part.replace(',', '').replace('.', ''))
                        except ValueError:
                            logger.error(f"Failed to parse points: {points_part}")
                            failed += 1
                            continue
                        
                        # Find user by username (multiple methods)
                        for member in interaction.guild.members:
                            if (member.display_name.lower() == username.lower() or 
                                member.name.lower() == username.lower() or
                                username.lower() in member.display_name.lower() or
                                username.lower() in member.name.lower()):
                                user = member
                                break
                
                # Pattern 2: 1. <@user_id> • points (for mentions with numbers)
                if '<@' in line and '•' in line:
                    logger.info(f"Trying regex on: {line}")
                    match = re.search(r'\d+\.\s*<@!?(\d+)>\s*•\s*([\d.,]+)', line)
                    if match:
                        logger.info(f"Regex matched: {match.groups()}")
                        user_id = int(match.group(1))
                        points_str = match.group(2)
                        
                        try:
                            points = float(points_str.replace(',', '').replace('.', ''))
                            user = interaction.guild.get_member(user_id)
                            logger.info(f"Found user: {user.display_name if user else 'None'}, points: {points}")
                        except ValueError:
                            logger.error(f"Failed to parse points from mention: {points_str}")
                            failed += 1
                            continue
                    else:
                        logger.warning(f"Regex did not match line: {line}")
                        # Try simpler pattern
                        simple_match = re.search(r'<@!?(\d+)>\s*•\s*([\d.,]+)', line)
                        if simple_match:
                            logger.info(f"Simple regex matched: {simple_match.groups()}")
                            user_id = int(simple_match.group(1))
                            points_str = simple_match.group(2)
                            
                            try:
                                points = float(points_str.replace(',', '').replace('.', ''))
                                user = interaction.guild.get_member(user_id)
                                logger.info(f"Found user: {user.display_name if user else 'None'}, points: {points}")
                            except ValueError:
                                logger.error(f"Failed to parse points from simple match: {points_str}")
                                failed += 1
                                continue
                        else:
                            logger.warning(f"Both regex patterns failed for: {line}")
                
                if not user or points is None:
                    if line.strip() and '•' in line:
                        failed += 1
                        logger.warning(f"Could not process line (no user or points): {line}")
                    continue
                
                try:
                    # Get multiplier setting
                    multiplier_data = await self.bot.db.multipliers.find_one({"guild_id": guild_id, "active": True})
                    multiplier = multiplier_data["multiplier"] if multiplier_data else 1.0
                    
                    # Calculate final points
                    final_points = points * multiplier
                    
                    # Get user's cult
                    user_cult_data = await self.bot.db.cults.find_one({
                        "guild_id": guild_id,
                        "members": user.id,
                        "active": True
                    })
                    
                    # Save points transaction
                    await self.bot.db.points.insert_one({
                        "user_id": user.id,
                        "user_name": str(user),
                        "guild_id": guild_id,
                        "guild_name": interaction.guild.name,
                        "amount": final_points,
                        "base_amount": points,
                        "multiplier_used": multiplier,
                        "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                        "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                        "type": "adminpoints",
                        "timestamp": datetime.now(timezone.utc)
                    })
                    
                    processed += 1
                    success_details.append(f"{user.display_name}: {final_points:,.0f} points")
                    
                    # Trigger reward check
                    try:
                        await self.bot.trigger_reward_check(user.id, guild_id)
                    except Exception as e:
                        logger.error(f"Error triggering reward check: {e}")
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Error processing user {user.display_name if user else 'Unknown'}: {e}")
            
            # Send detailed confirmation
            if processed > 0:
                embed = discord.Embed(
                    title="✅ Admin Points Added",
                    description=f"Successfully processed **{processed}** users\nFailed: **{failed}** entries",
                    color=0x00ff00
                )
                
                if success_details:
                    details_text = "\n".join(success_details[:10])
                    if len(success_details) > 10:
                        details_text += f"\n...and {len(success_details) - 10} more"
                    embed.add_field(name="Details", value=details_text, inline=False)
                
                embed.add_field(name="Processed by", value=interaction.user.mention, inline=True)
                embed.add_field(name="Server", value=interaction.guild.name, inline=True)
            else:
                embed = discord.Embed(
                    title="❌ No Points Added",
                    description=f"Failed to process any users from the message\nFailed entries: {failed}",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Critical error in adminpoints command: {e}")
            try:
                await interaction.followup.send(f"❌ Critical error occurred: {str(e)[:100]}...", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(AdminPoints(bot))