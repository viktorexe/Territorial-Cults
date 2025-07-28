import discord
from discord.ext import commands
from discord import app_commands

class MultiplierInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="multiplier_info", description="Show current multiplier information")
    async def multiplier_info(self, interaction: discord.Interaction):
        try:
            if self.bot.db is None:
                await interaction.response.send_message("❌ Database not available!", ephemeral=True)
                return
            
            if not interaction.guild:
                await interaction.response.send_message("❌ This command can only be used in servers!", ephemeral=True)
                return
            
            guild_id = interaction.guild.id
            
            # Get active multiplier
            multiplier_data = await self.bot.db.multipliers.find_one({
                "guild_id": guild_id,
                "active": True
            })
            
            embed = discord.Embed(color=0x00ff00)
            embed.set_author(
                name=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            if not multiplier_data:
                embed.title = "❌ No Active Multiplier"
                embed.description = "No multiplier is currently active in this server."
                embed.color = 0x2b2d31
            else:
                embed.title = f"✅ Active Multiplier: {multiplier_data['multiplier']}x"
                embed.description = multiplier_data['description']
                
                embed.add_field(
                    name="Set by",
                    value=f"<@{multiplier_data['set_by']}>",
                    inline=True
                )
                
                embed.add_field(
                    name="Started",
                    value=f"<t:{int(multiplier_data['timestamp'].timestamp())}:R>",
                    inline=True
                )
                
                if 'edited_by' in multiplier_data:
                    embed.add_field(
                        name="Last Edited",
                        value=f"<t:{int(multiplier_data['edit_timestamp'].timestamp())}:R>",
                        inline=True
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            try:
                await interaction.response.send_message("❌ An error occurred while loading multiplier info!", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred while loading multiplier info!", ephemeral=True)
            print(f"Error in multiplier_info command: {e}")

async def setup(bot):
    await bot.add_cog(MultiplierInfo(bot))