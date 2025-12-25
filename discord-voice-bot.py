import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='.v ', intents=intents)

# Store voice channel ownership data
voice_channels = {}
DATA_FILE = 'voice_channels.json'

# Load saved data
def load_data():
    global voice_channels
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            voice_channels = json.load(f)

# Save data
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(voice_channels, f)

# Control Panel View with Buttons
class VoiceControlPanel(discord.ui.View):
    def __init__(self, channel_id, owner_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.owner_id = owner_id
    
    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, custom_id="lock")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("🔒 Room locked!", ephemeral=True)
    
    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success, custom_id="unlock")
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message("🔓 Room unlocked!", ephemeral=True)
    
    @discord.ui.button(label="👁️ Hide", style=discord.ButtonStyle.secondary, custom_id="hide")
    async def hide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("👁️ Room hidden!", ephemeral=True)
    
    @discord.ui.button(label="👁️‍🗨️ Unhide", style=discord.ButtonStyle.secondary, custom_id="unhide")
    async def unhide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            await interaction.response.send_message("👁️‍🗨️ Room visible!", ephemeral=True)

# Modal for setting user limit
class LimitModal(discord.ui.Modal, title="Set User Limit"):
    limit = discord.ui.TextInput(label="User Limit (0 for unlimited)", placeholder="Enter a number between 0-99", max_length=2)
    
    def __init__(self, channel_id, owner_id):
        super().__init__()
        self.channel_id = channel_id
        self.owner_id = owner_id
    
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        try:
            limit_value = int(self.limit.value)
            if limit_value < 0 or limit_value > 99:
                await interaction.response.send_message("❌ Limit must be between 0-99!", ephemeral=True)
                return
            
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.edit(user_limit=limit_value)
                await interaction.response.send_message(f"✅ User limit set to {limit_value if limit_value > 0 else 'unlimited'}!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)

# Extended Control Panel with More Options
class ExtendedControlPanel(discord.ui.View):
    def __init__(self, channel_id, owner_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.owner_id = owner_id
    
    @discord.ui.button(label="👥 Set Limit", style=discord.ButtonStyle.primary, custom_id="limit")
    async def limit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        await interaction.response.send_modal(LimitModal(self.channel_id, self.owner_id))
    
    @discord.ui.button(label="🚫 Reject User", style=discord.ButtonStyle.danger, custom_id="reject")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        await interaction.response.send_message("Use command: `.v reject @user` to reject a user", ephemeral=True)
    
    @discord.ui.button(label="👢 Kick User", style=discord.ButtonStyle.danger, custom_id="kick")
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        await interaction.response.send_message("Use command: `.v kick @user` to kick a user", ephemeral=True)
    
    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="rename")
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the room owner can use this!", ephemeral=True)
            return
        
        await interaction.response.send_message("Use command: `.v name New Room Name` to rename", ephemeral=True)

@bot.event
async def on_ready():
    load_data()
    print(f'{bot.user} is now online!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# Slash command to create voice channel
@bot.tree.command(name="createvoice", description="Create your own custom voice channel")
async def create_voice(interaction: discord.Interaction):
    guild = interaction.guild
    category = interaction.channel.category
    
    # Create voice channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
        interaction.user: discord.PermissionOverwrite(
            connect=True,
            manage_channels=True,
            manage_permissions=True,
            move_members=True
        )
    }
    
    voice_channel = await guild.create_voice_channel(
        name=f"{interaction.user.display_name}'s Room",
        category=category,
        overwrites=overwrites
    )
    
    # Create text channel for controls
    text_channel = await guild.create_text_channel(
        name=f"{interaction.user.display_name}-room-chat",
        category=category,
        overwrites=overwrites
    )
    
    # Store channel data
    voice_channels[str(voice_channel.id)] = {
        'owner_id': interaction.user.id,
        'text_channel_id': text_channel.id,
        'guild_id': guild.id
    }
    save_data()
    
    # Send control panels to text channel
    embed1 = discord.Embed(
        title="🎮 Voice Room Control Panel",
        description=f"**Room Owner:** {interaction.user.mention}\n**Voice Channel:** {voice_channel.mention}\n\nUse the buttons below to control your room!",
        color=discord.Color.blue()
    )
    embed1.add_field(name="🔒 Lock/Unlock", value="Control who can join", inline=True)
    embed1.add_field(name="👁️ Hide/Unhide", value="Control visibility", inline=True)
    
    embed2 = discord.Embed(
        title="⚙️ Advanced Controls",
        description="Additional room management options",
        color=discord.Color.green()
    )
    embed2.add_field(name="Commands", value=(
        "`.v reject @user` - Block user from joining\n"
        "`.v allow @user` - Allow blocked user\n"
        "`.v kick @user` - Kick user from room\n"
        "`.v name New Name` - Rename room\n"
        "`.v limit 5` - Set user limit\n"
        "`.v permit @user` - Grant control permissions\n"
        "`.v claim` - Claim ownership if owner left"
    ), inline=False)
    
    await text_channel.send(embed=embed1, view=VoiceControlPanel(voice_channel.id, interaction.user.id))
    await text_channel.send(embed=embed2, view=ExtendedControlPanel(voice_channel.id, interaction.user.id))
    
    await interaction.response.send_message(
        f"✅ Created your voice room! {voice_channel.mention}\n"
        f"📝 Control panel: {text_channel.mention}",
        ephemeral=True
    )

# Helper function to check ownership
def is_owner(channel_id, user_id):
    channel_data = voice_channels.get(str(channel_id))
    return channel_data and channel_data['owner_id'] == user_id

# Text Commands
@bot.command(name='reject')
async def reject_user(ctx, member: discord.Member):
    """Block a user from joining your voice room"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    channel = voice_state.channel
    await channel.set_permissions(member, connect=False, view_channel=True)
    await ctx.send(f"🚫 {member.mention} has been rejected from the room!")

@bot.command(name='allow')
async def allow_user(ctx, member: discord.Member):
    """Allow a blocked user to join your voice room"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    channel = voice_state.channel
    await channel.set_permissions(member, connect=True)
    await ctx.send(f"✅ {member.mention} can now join the room!")

@bot.command(name='kick')
async def kick_user(ctx, member: discord.Member):
    """Kick a user from your voice room"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    if member.voice and member.voice.channel.id == channel_id:
        await member.move_to(None)
        await ctx.send(f"👢 {member.mention} has been kicked from the room!")
    else:
        await ctx.send(f"❌ {member.mention} is not in your room!")

@bot.command(name='name')
async def rename_channel(ctx, *, new_name: str):
    """Rename your voice room"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    channel = voice_state.channel
    await channel.edit(name=new_name)
    await ctx.send(f"✏️ Room renamed to: **{new_name}**")

@bot.command(name='limit')
async def set_limit(ctx, limit: int):
    """Set user limit for your voice room (0 for unlimited)"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    if limit < 0 or limit > 99:
        await ctx.send("❌ Limit must be between 0-99!")
        return
    
    channel = voice_state.channel
    await channel.edit(user_limit=limit)
    await ctx.send(f"👥 User limit set to: **{limit if limit > 0 else 'unlimited'}**")

@bot.command(name='permit')
async def grant_permissions(ctx, member: discord.Member):
    """Grant control permissions to another user"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = voice_state.channel.id
    if not is_owner(channel_id, ctx.author.id):
        await ctx.send("❌ You don't own this voice room!")
        return
    
    channel = voice_state.channel
    await channel.set_permissions(member, 
        connect=True,
        manage_channels=True,
        manage_permissions=True,
        move_members=True
    )
    await ctx.send(f"✅ {member.mention} has been granted control permissions!")

@bot.command(name='claim')
async def claim_ownership(ctx):
    """Claim ownership of a voice room if the owner left"""
    voice_state = ctx.author.voice
    if not voice_state or not voice_state.channel:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    channel_id = str(voice_state.channel.id)
    if channel_id not in voice_channels:
        await ctx.send("❌ This is not a custom voice room!")
        return
    
    owner_id = voice_channels[channel_id]['owner_id']
    owner = ctx.guild.get_member(owner_id)
    
    # Check if owner is still in the channel
    if owner and owner.voice and owner.voice.channel.id == int(channel_id):
        await ctx.send("❌ The owner is still in the room!")
        return
    
    # Transfer ownership
    voice_channels[channel_id]['owner_id'] = ctx.author.id
    save_data()
    
    channel = voice_state.channel
    await channel.set_permissions(ctx.author,
        connect=True,
        manage_channels=True,
        manage_permissions=True,
        move_members=True
    )
    await ctx.send(f"✅ {ctx.author.mention} is now the room owner!")

# Auto-delete channels when empty
@bot.event
async def on_voice_state_update(member, before, after):
    # Check if someone left a channel
    if before.channel and str(before.channel.id) in voice_channels:
        if len(before.channel.members) == 0:
            # Channel is empty, delete it
            channel_data = voice_channels[str(before.channel.id)]
            text_channel = bot.get_channel(channel_data['text_channel_id'])
            
            try:
                await before.channel.delete()
                if text_channel:
                    await text_channel.delete()
                del voice_channels[str(before.channel.id)]
                save_data()
            except Exception as e:
                print(f"Error deleting channels: {e}")

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("❌ Please set DISCORD_BOT_TOKEN environment variable")
    else:
        bot.run(TOKEN)
