import discord
from discord.ext import commands
from discord import app_commands

class ListRewardsView(discord.ui.View):
    def __init__(self, rewards, guild):
        super().__init__(timeout=300)
        self.guild = guild
        self.page = 0
        self.per_page = 8
        
        # Separate rewards by type and sort
        self.points_rewards = sorted([r for r in rewards if r["type"] == "points"], key=lambda x: x["amount"])
        self.wins_rewards = sorted([r for r in rewards if r["type"] == "wins"], key=lambda x: x["amount"])
        
        # Calculate pages
        self.points_pages = max(1, (len(self.points_rewards) + self.per_page - 1) // self.per_page) if self.points_rewards else 0
        self.wins_pages = max(1, (len(self.wins_rewards) + self.per_page - 1) // self.per_page) if self.wins_rewards else 0
        self.total_pages = self.points_pages + self.wins_pages
        
        if self.total_pages <= 1:
            self.clear_items()
    
    def get_page_data(self):
        if self.page < self.points_pages:
            # Points page
            start = self.page * self.per_page
            end = start + self.per_page
            return self.points_rewards[start:end], "points"
        else:
            # Wins page
            wins_page = self.page - self.points_pages
            start = wins_page * self.per_page
            end = start + self.per_page
            return self.wins_rewards[start:end], "wins"
    
    def create_embed(self):
        page_rewards, reward_type = self.get_page_data()
        
        if reward_type == "points":
            embed = discord.Embed(
                title="📊 Points Reward Configuration",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="🏆 Wins Reward Configuration",
                color=0xffa500
            )
        
        # Calculate starting number for this page
        if reward_type == "points":
            start_num = self.page * self.per_page + 1
        else:
            start_num = (self.page - self.points_pages) * self.per_page + 1
        
        for i, reward in enumerate(page_rewards, start=start_num):
            role = self.guild.get_role(reward["role_id"])
            channel = self.guild.get_channel(reward["channel_id"])
            
            field_value = f"Role: {role.mention if role else '❌ Deleted'}\nChannel: {channel.mention if channel else '❌ Deleted'}"
            
            embed.add_field(
                name=f"{i}. {reward['amount']:,} {reward_type.title()}",
                value=field_value,
                inline=True
            )
        
        total_rewards = len(self.points_rewards) + len(self.wins_rewards)
        if self.total_pages > 1:
            embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages} • Total: {total_rewards} rewards")
        else:
            embed.set_footer(text=f"Total: {total_rewards} rewards")
        
        return embed
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.total_pages - 1:
            self.page += 1
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

class ListRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="listrewards", description="List reward roles (Bot Manager required)")
    async def listrewards(self, interaction: discord.Interaction):
        # Import here to avoid circular import
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from utils.permissions import check_bot_manager
        
        if not await check_bot_manager(self.bot, interaction):
            await interaction.response.send_message("❌ You need Bot Manager role to use this command!", ephemeral=True)
            return
        
        rewards = await self.bot.db.reward_roles.find({"guild_id": interaction.guild.id, "active": True}).to_list(None)
        
        if not rewards:
            await interaction.response.send_message("❌ No reward roles set up!", ephemeral=True)
            return
        
        # Sort rewards by type and amount
        rewards.sort(key=lambda x: (x["type"], x["amount"]))
        
        view = ListRewardsView(rewards, interaction.guild)
        embed = view.create_embed()
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ListRewards(bot))