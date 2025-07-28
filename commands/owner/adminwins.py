import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger('TerritorialBot')

class AdminWins(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="adminwins", description="Add wins from leaderboard message")
    @app_commands.describe(message_id="Message ID of the leaderboard")
    async def adminwins(self, interaction: discord.Interaction, message_id: str):
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
            
            # Parse leaderboard entries
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Leaderboard') or line.startswith('Showing') or line == '⠀':
                    continue
                
                user = None
                wins = None
                
                # Pattern: 1. <@user_id> • wins
                if '<@' in line and '•' in line:
                    simple_match = re.search(r'<@!?(\d+)>\s*•\s*([\d.,]+)', line)
                    if simple_match:
                        user_id = int(simple_match.group(1))
                        wins_str = simple_match.group(2)
                        
                        try:
                            wins = int(wins_str.replace(',', '').replace('.', ''))
                            user = interaction.guild.get_member(user_id)
                        except ValueError:
                            logger.error(f"Failed to parse wins: {wins_str}")
                            failed += 1
                            continue
                
                if not user or wins is None:
                    if line.strip() and '•' in line:
                        failed += 1
                    continue
                
                try:
                    # Get user's cult
                    user_cult_data = await self.bot.db.cults.find_one({
                        "guild_id": guild_id,
                        "members": user.id,
                        "active": True
                    })
                    
                    # Save win transaction
                    await self.bot.db.wins.insert_one({
                        "user_id": user.id,
                        "user_name": str(user),
                        "guild_id": guild_id,
                        "guild_name": interaction.guild.name,
                        "amount": wins,
                        "cult_id": str(user_cult_data["_id"]) if user_cult_data else None,
                        "cult_name": user_cult_data["cult_name"] if user_cult_data else None,
                        "type": "adminwins",
                        "timestamp": datetime.now(timezone.utc)
                    })
                    
                    processed += 1
                    success_details.append(f"{user.display_name}: {wins:,} wins")
                    
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
                    title="✅ Admin Wins Added",
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
                    title="❌ No Wins Added",
                    description=f"Failed to process any users from the message\nFailed entries: {failed}",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Critical error in adminwins command: {e}")
            try:
                await interaction.followup.send(f"❌ Critical error occurred: {str(e)[:100]}...", ephemeral=True)
            except:
                pass

async def setup(bot):
    await bot.add_cog(AdminWins(bot))