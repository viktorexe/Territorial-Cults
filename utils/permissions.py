async def check_bot_manager(bot, interaction):
    """Check if user is bot manager or special user"""
    # Special user always allowed
    if interaction.user.id == 780678948949721119:
        return True
    
    if bot.db is None:
        print(f"DEBUG: Database not available for user {interaction.user.id}")
        return False
    
    # Get bot manager role for this guild
    settings = await bot.db.bot_settings.find_one({"guild_id": interaction.guild.id})
    print(f"DEBUG: Settings for guild {interaction.guild.id}: {settings}")
    
    if not settings or not settings.get("manager_role_id"):
        print(f"DEBUG: No bot manager role set for guild {interaction.guild.id}")
        return False
    
    # Check if user has bot manager role
    manager_role = interaction.guild.get_role(settings["manager_role_id"])
    user_roles = [role.id for role in interaction.user.roles]
    print(f"DEBUG: Manager role: {settings['manager_role_id']}, User roles: {user_roles}")
    
    has_role = manager_role and manager_role in interaction.user.roles
    print(f"DEBUG: User {interaction.user.id} has bot manager role: {has_role}")
    
    return has_role