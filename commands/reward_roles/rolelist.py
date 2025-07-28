import discord
from discord.ext import commands
from discord import app_commands

class RoleListView(discord.ui.View):
    def __init__(self, rewards, guild):
        super().__init__(timeout=300)
        self.guild = guild
        self.page = 0
        self.per_page = 10
        
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
                title=f"📊 Points Reward Roles - {self.guild.name}",
                color=0x00ff00
            )
            icon = "📊"
        else:
            embed = discord.Embed(
                title=f"🏆 Wins Reward Roles - {self.guild.name}",
                color=0xffa500
            )
            icon = "🏆"
        
        embed.set_author(
            name=self.guild.name,
            icon_url=self.guild.icon.url if self.guild.icon else None
        )
        
        rewards_text = ""
        for reward in page_rewards:
            role = self.guild.get_role(reward["role_id"])
            if role:
                rewards_text += f"{role.mention} - {reward['amount']:,} {reward_type}\n"
        
        if rewards_text:
            embed.description = rewards_text
        else:
            embed.description = f"No {reward_type} rewards found."
        
        if self.total_pages > 1:
            embed.set_footer(text=f"Page {self.page + 1}/{self.total_pages}")
        
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

class RoleList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rolelist", description="List all reward roles and requirements")
    async def rolelist(self, interaction: discord.Interaction):
        rewards = await self.bot.db.reward_roles.find({"guild_id": interaction.guild.id, "active": True}).to_list(None)
        
        if not rewards:
            await interaction.response.send_message("No reward roles available!", ephemeral=True)
            return
        
        view = RoleListView(rewards, interaction.guild)
        embed = view.create_embed()
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RoleList(bot))