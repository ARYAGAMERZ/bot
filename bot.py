import discord
from discord.ext import commands
import pyfiglet
from collections import defaultdict, deque
import asyncio
import yt_dlp as youtube_dl
import aiohttp
import time
from discord import FFmpegPCMAudio, ButtonStyle, Interaction
from discord.ui import Button, View
import re
import lyricsgenius
import nacl  # Make sure PyNaCl is imported



intents = discord.Intents.all()
client = commands.Bot(command_prefix=['!', '+'], intents=intents)

message_tracker = defaultdict(lambda: deque(maxlen=5))
user_timeouts = defaultdict(lambda: 60)  # Start with a 1-minute timeout
SPAM_WINDOW = 10  # Time window in seconds to monitor for spam
SPAM_THRESHOLD = 5  # Number of messages allowed per SPAM_WINDOW seconds

# Custom check to allow only the owner to use certain commands
def is_owner():
    async def predicate(ctx):
        return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id
    return commands.check(predicate)

# Fetch GIF function
async def fetch_gif(keyword: str) -> str:
    try:
        url = f'https://api.tenor.com/v1/random?q={keyword}&key=LIVDSRZULELA&limit=1'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data['results'][0]['media'][0]['gif']['url']
    except Exception as e:
        print(f"Exception occurred while fetching GIF: {e}")
        return None

genius = lyricsgenius.Genius('28jwoKAkskaSjsnsksAjnwjUJwj')  # Replace with your Genius API token

@client.command(name='lyrics', help='Fetches the lyrics of the currently playing song')
async def lyrics(ctx):
    if music_queue.current:
        song_title = music_queue.current.title
        try:
            song = genius.search_song(song_title)
            if song:
                lyrics = song.lyrics
                # Truncate lyrics to fit Discord message limits
                if len(lyrics) > 2000:
                    lyrics = lyrics[:2000] + '...'
                await ctx.send(f'**Lyrics for {song_title}:**\n{lyrics}')
            else:
                await ctx.send(f'Could not find lyrics for {song_title}')
        except Exception as e:
            await ctx.send(f'Error fetching lyrics: {str(e)}')
    else:
        await ctx.send('No song is currently playing')

@client.command()
async def help_command(ctx):
    gif_url = "https://media.tenor.com/678HXnTaB_oAAAAi/nova-novacat.gif"
    embed = discord.Embed(title="Command Help", description="React with buttons below or use commands to perform actions", color=0x00ff00)
    embed.set_image(url=gif_url)
    embed.add_field(name="Command Help", value="React with buttons below or use commands to perform actions", inline=False)
    embed.add_field(name="Kick", value="React with ⚒️ or use `+kick @user` to kick a user", inline=False)
    embed.add_field(name="Ban", value="React with 🚫 or use `+ban @user` to ban a user", inline=False)
    embed.add_field(name="Mute", value="React with 🔇 or use `+mute @user` to mute a user", inline=False)
    embed.add_field(name="Unmute", value="React with 🔊 or use `+unmute @user` to unmute a user", inline=False)
    embed.add_field(name="Disconnect", value="React with ❌ or use `+disconnect @user` to disconnect user from voice channel", inline=False)
    embed.add_field(name="Purge", value="Delete a specified number of messages using `+purge <amount>`", inline=False)
    embed.add_field(name="Nickname", value="Change a user's nickname using `+nickname @user <new_nickname>`", inline=False)
    embed.add_field(name="Server Info", value="Get information about the server with `!server_info`", inline=False)
    embed.add_field(name="User Info", value="Get information about a user with `!user_info @user`", inline=False)
    embed.add_field(name="Timeout", value="To give Timeout to a User `+timeout @user <sec>`", inline=False)
    embed.add_field(name="Say", value="Make the bot repeat a message with `!say <message>`", inline=False)
    embed.add_field(name="Auto-Moderation", value="Automatically moderates the server. No setup required.", inline=False)
    embed.add_field(name="Polls", value="Create a poll with `+poll <question> <option1> <option2> ...`", inline=False)
    embed.add_field(name="Welcome", value="Welcomes new members to the server.", inline=False)
    embed.add_field(name="Farewell", value="Bids farewell to departing members.", inline=False)
    embed.add_field(name="Movevc", value="Move a user to another voice channel with `+movevc @user`", inline=False)
    embed.add_field(name="Create Role", value="Create a new role with `+createrole <rolename> <colour>`", inline=False)
    embed.add_field(name="Give Role", value="Give a role to a user with `+giveroll @user <rolename>`", inline=False)
    embed.add_field(name="Remove Role", value="Remove a role from a user with `+removeroll @user <rolename>`", inline=False)
    embed.add_field(name="Join", value="Bot joins your voice channel with `!join`", inline=False)
    embed.add_field(name="Leave", value="Bot leaves the voice channel with `!leave`", inline=False)
    
    message = await ctx.send(embed=embed)
    emojis = ['⚒️', '🚫', '🔇', '🔊', '❌']
    for emoji in emojis:
        await message.add_reaction(emoji)


# Owner restricted commands
@client.command(name='kick')
@is_owner()
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send(f'{member.mention} has been kicked.')

@client.command(name='ban')
@is_owner()
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send(f'{member.mention} has been banned.')

@client.command(name='mute')
@is_owner()
async def mute(ctx, member: discord.Member):
    # Implement mute logic here
    await ctx.send(f'{member.mention} has been muted.')

@client.command(name='unmute')
@is_owner()
async def unmute(ctx, member: discord.Member):
    # Implement unmute logic here
    await ctx.send(f'{member.mention} has been unmuted.')

@client.command(name='disconnect')
@is_owner()
async def disconnect(ctx, member: discord.Member):
    await member.move_to(None)
    await ctx.send(f'{member.mention} has been disconnected from the voice channel.')

@client.command(name='purge')
@is_owner()
async def purge(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)  # +1 to also remove the command message
    await ctx.send(f'{amount} messages deleted.')

@client.command(name='nickname')
@is_owner()
async def nickname(ctx, member: discord.Member, *, new_nickname):
    await member.edit(nick=new_nickname)
    await ctx.send(f'{member.mention}\'s nickname has been changed to {new_nickname}.')

@client.command(name='unban')
@is_owner()
async def unban(ctx, user: discord.User):   
    try:
        await ctx.guild.unban(user)
        await ctx.send(f"{user.mention} has been unbanned.")
    except discord.NotFound:
        await ctx.send("User not found. Please ensure you provided a valid user.")
    except discord.Forbidden:
        await ctx.send("Bot does not have permission to unban users.")
    except discord.HTTPException:
        await ctx.send("An error occurred while processing the unban.")

@client.command(name='timeout')
@is_owner()
async def timeout(ctx, user: discord.Member, duration: int):
    try:
        if duration <= 0:
            await ctx.send("Error: Duration must be a positive integer.")
            return

        timeout_role = discord.utils.get(ctx.guild.roles, name="Timeout")
        if timeout_role is None:
            timeout_role = await ctx.guild.create_role(name="Timeout")

        for channel in ctx.guild.channels:
            await channel.set_permissions(user, send_messages=False, connect=False)

        timeout_message = await ctx.send(f"{user.mention} has been timed out for {duration} seconds.")

        for remaining_time in range(duration, 0, -1):
            await asyncio.sleep(1)  # Wait for 1 second
            await timeout_message.edit(content=f"{user.mention} has been timed out for {remaining_time} seconds.")

        for channel in ctx.guild.channels:
            await channel.set_permissions(user, overwrite=None)

        await ctx.send(f"{user.mention}'s timeout has ended.")
    except ValueError:
        await ctx.send("Error: Invalid duration provided. Please provide a valid positive integer value for duration.")

@client.command(name='createrole')
@is_owner()
async def createrole(ctx, role_name, color: discord.Colour = None):
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You don't have permission to manage roles.")
        return

    existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
    if existing_role:
        await ctx.send("A role with the same name already exists.")
        return

    try:
        new_role = await ctx.guild.create_role(name=role_name, color=color)
        await ctx.send(f"Role `{role_name}` has been created.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage roles.")
    except discord.HTTPException:
        await ctx.send("Failed to create the role. An error occurred.")

@client.command(name='giveroll')
@is_owner()
async def giveroll(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You don't have permission to manage roles.")
        return

    roles = ctx.guild.roles
    options_message = "Select the role you want to give to the user:\n"
    for index, role in enumerate(roles, start=1):
        options_message += f"{index}. {role.name}\n"

    options_embed = discord.Embed(title="Role Options", description=options_message, color=0x00ff00)
    options_embed.set_footer(text="Type the number corresponding to the desired role.")
    options_message = await ctx.send(embed=options_embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        response = await client.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Command cancelled.")
        return

    try:
        selection = int(response.content)
        if selection < 1 or selection > len(roles):
            await ctx.send("Invalid selection.")
            return
        selected_role = roles[selection - 1]
    except ValueError:
        await ctx.send("Invalid input. Please enter a number.")
        return

    try:
        await member.add_roles(selected_role)
        await ctx.send(f"Role `{selected_role.name}` has been given to {member.mention}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage this roles.")
    except discord.HTTPException:
        await ctx.send("Failed to give the role. An error occurred.")

@client.command(name='removeroll')
@is_owner()
async def removeroll(ctx, member: discord.Member):
    if not ctx.author.guild_permissions.manage_roles:
        await ctx.send("You don't have permission to manage roles.")
        return

    user_roles = member.roles[1:]  # Exclude @everyone role
    if len(user_roles) == 0:
        await ctx.send(f"{member.display_name} doesn't have any roles to remove.")
        return

    options_message = "Select the role you want to remove from the user:\n"
    for index, role in enumerate(user_roles, start=1):
        options_message += f"{index}. {role.name}\n"

    options_embed = discord.Embed(title="Role Removal", description=options_message, color=0x00ff00)
    options_embed.set_footer(text="Type the number corresponding to the desired role.")
    options_message = await ctx.send(embed=options_embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        response = await client.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Command cancelled.")
        return

    try:
        selection = int(response.content)
        if selection < 1 or selection > len(user_roles):
            await ctx.send("Invalid selection. Please select a number within the range.")
            return
        selected_role = user_roles[selection - 1]
    except ValueError:
        await ctx.send("Invalid input. Please enter a number.")
        return

    try:
        await member.remove_roles(selected_role)
        await ctx.send(f"Role `{selected_role.name}` has been removed from {member.mention}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage roles.")
    except discord.HTTPException:
        await ctx.send("Failed to remove the role. An error occurred.")

@client.command(name='movevc')
@is_owner()
async def movevc(ctx, member: discord.Member):
    voice_channels = ctx.guild.voice_channels
    if not voice_channels:
        await ctx.send("There are no voice channels in this server.")
        return

    options_message = "Select the destination voice channel:\n"
    for index, channel in enumerate(voice_channels, start=1):
        options_message += f"{index}. {channel.name}\n"

    options_embed = discord.Embed(title="Voice Channel Options", description=options_message, color=0x00ff00)
    options_embed.set_footer(text="Type the number corresponding to the desired voice channel.")
    options_message = await ctx.send(embed=options_embed)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        response = await client.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Command cancelled.")
        return

    try:
        selection = int(response.content)
        if selection < 1 or selection > len(voice_channels):
            await ctx.send("Invalid selection. Please select a number within the range.")
            return
        target_channel = voice_channels[selection - 1]
    except ValueError:
        await ctx.send("Invalid input. Please enter a number.")
        return

    if not member.voice:
        await ctx.send(f"{member.display_name} is not in a voice channel.")
        return

    try:
        await member.move_to(target_channel)
        await ctx.send(f"{member.display_name} has been moved to {target_channel.name}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to move members.")
    except discord.HTTPException:
        await ctx.send("Failed to move the member. An error occurred.")

@client.command(name='poll')
@is_owner()
async def poll(ctx, *, question_and_options):
    parts = question_and_options.split("::")
    question = parts[0].strip()
    options = [opt.strip() for opt in parts[1].split(',')]

    if len(options) < 2:
        await ctx.send("Please provide at least two options for the poll.")
        return

    poll_embed = discord.Embed(title=question, color=0x00ff00)
    for option in options:
        poll_embed.add_field(name='\u200b', value=option, inline=False)
    poll_message = await ctx.send(embed=poll_embed)

    for i in range(len(options)):
        await poll_message.add_reaction(chr(0x1f1e6 + i))


# Music commands
youtube_dl_options = {
    'format': 'bestaudio/best',
    'noplaylist': False,  # Allow playlists
    'restrictfilenames': True,
    'no_warnings': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(youtube_dl_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data['title']
        self.url = data['url']

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # It's a playlist
            entries = data['entries']
            songs = [cls(discord.FFmpegPCMAudio(entry['url']), data=entry) for entry in entries]
            return songs
        else:
            # It's a single video
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return [cls(discord.FFmpegPCMAudio(filename), data=data)]

class MusicQueue:
    def __init__(self):
        self.queue = deque()  # Using deque for easier manipulation
        self.is_playing = False
        self.loop = False
        self.current = None

    def add(self, player):
        self.queue.append(player)

    def get_next(self):
        if self.loop:
            return self.current  # Return the current song if looping
        return self.queue.popleft() if self.queue else None

    def is_empty(self):
        return len(self.queue) == 0

    def toggle_loop(self):
        self.loop = not self.loop
        return self.loop

music_queue = MusicQueue()

async def play_next(ctx):
    player = music_queue.get_next()
    if player:
        music_queue.is_playing = True
        music_queue.current = player  # Set the current playing song
        ctx.voice_client.play(player, after=lambda e: client.loop.create_task(play_next(ctx)))
        await ctx.send(f'Now playing: {player.title}')
    else:
        music_queue.is_playing = False
        music_queue.current = None  # Clear the current song when the queue is empty and not looping

@client.command(name='join', help='Joins the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send(f'{ctx.author.name} is not connected to a voice channel')
        return
    else:
        channel = ctx.message.author.voice.channel

    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

@client.command(name='leave', help='Leaves the voice channel')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel")
    else:
        await ctx.send("Not connected to a voice channel")

@client.command(name='play', help='Plays a song or a YouTube playlist')
async def play(ctx, *, query):
    if ctx.voice_client is None:
        await ctx.send("Bot is not connected to a voice channel. Use `!join` to invite the bot.")
        return

    async with ctx.typing():
        players = await YTDLSource.from_url(query, loop=client.loop, stream=True)
        for player in players:
            music_queue.add(player)
        
        if not ctx.voice_client.is_playing() and not music_queue.is_empty():
            music_queue.is_playing = True
            await play_next(ctx)
        else:
            await ctx.send(f'Added {len(players)} songs to the queue.')

@client.command(name='skip', help='Skips the current song')
async def skip(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        await ctx.send("No song is currently playing")
    else:
        ctx.voice_client.stop()
        await ctx.send("Skipped the song")

@client.command(name='queue', help='Shows the current song queue')
async def show_queue(ctx):
    if music_queue.is_empty():
        await ctx.send("The queue is empty")
    else:
        queue_titles = [player.title for player in music_queue.queue]
        await ctx.send("Current queue:\n" + "\n".join(queue_titles))

@client.command(name='clear', help='Clears the song queue')
async def clear(ctx):
    music_queue.queue.clear()
    await ctx.send("Cleared the queue")

@client.command(name='pause', help='Pauses the song')
async def pause(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        await ctx.send("No song is currently playing")
    else:
        ctx.voice_client.pause()
        await ctx.send("Paused the song")

@client.command(name='resume', help='Resumes the song')
async def resume(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_paused():
        await ctx.send("The song is not paused")
    else:
        ctx.voice_client.resume()
        await ctx.send("Resumed the song")

@client.command(name='stop', help='Stops the song')
async def stop(ctx):
    if ctx.voice_client is None or not ctx.voice_client.is_playing():
        await ctx.send("No song is currently playing")
    else:
        ctx.voice_client.stop()
        await ctx.send("Stopped the song")

@client.command(name='volume', help='Changes the volume of the bot')
async def volume(ctx, volume: int):
    if ctx.voice_client is None or ctx.voice_client.source is None:
        await ctx.send("Not connected to a voice channel or no audio source available")
    else:
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

class MusicView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.loop_button.label = 'Loop'  # Initialize the button label

    @discord.ui.button(label='Pause', style=ButtonStyle.blurple)
    async def pause_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("Paused the song", ephemeral=True)
        else:
            await interaction.response.send_message("No song is currently playing", ephemeral=True)

    @discord.ui.button(label='Resume', style=ButtonStyle.blurple)
    async def resume_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("Resumed the song", ephemeral=True)
        else:
            await interaction.response.send_message("The song is not paused", ephemeral=True)

    @discord.ui.button(label='Stop', style=ButtonStyle.red)
    async def stop_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            await interaction.response.send_message("Stopped the song", ephemeral=True)
        else:
            await interaction.response.send_message("No song is currently playing", ephemeral=True)

    @discord.ui.button(label='Skip', style=ButtonStyle.grey)
    async def skip_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            await interaction.response.send_message("Skipped the song", ephemeral=True)
        else:
            await interaction.response.send_message("No song is currently playing", ephemeral=True)

    @discord.ui.button(label='Volume Up', style=ButtonStyle.grey)
    async def volume_up_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.source:
            new_volume = min(self.ctx.voice_client.source.volume + 0.1, 1.0)
            self.ctx.voice_client.source.volume = new_volume
            await interaction.response.send_message(f"Volume set to {int(new_volume * 100)}%", ephemeral=True)

    @discord.ui.button(label='Volume Down', style=ButtonStyle.grey)
    async def volume_down_button(self, interaction: Interaction, button: Button):
        if self.ctx.voice_client and self.ctx.voice_client.source:
            new_volume = max(self.ctx.voice_client.source.volume - 0.1, 0.0)
            self.ctx.voice_client.source.volume = new_volume
            await interaction.response.send_message(f"Volume set to {int(new_volume * 100)}%", ephemeral=True)

    @discord.ui.button(label='Loop', style=ButtonStyle.green)
    async def loop_button(self, interaction: Interaction, button: Button):
        loop_status = music_queue.toggle_loop()
        if loop_status:
            button.label = 'Unloop'
            await interaction.response.send_message("Looping is now enabled", ephemeral=True)
        else:
            button.label = 'Loop'
            await interaction.response.send_message("Looping is now disabled", ephemeral=True)
        await interaction.message.edit(view=self)

@client.command(name='search', help='Searches for a song and lets you choose from the results')
async def search(ctx, *, query):
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status == 200:
                html = await response.text()
                video_ids = re.findall(r"watch\?v=(\S{11})", html)
                if not video_ids:
                    await ctx.send("No results found")
                    return
                choices = [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids[:5]]
                await ctx.send("Choose a song:\n" + "\n".join([f"{i+1}: {choices[i]}" for i in range(len(choices))]))

                def check(m):
                    return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(choices)

                try:
                    msg = await client.wait_for('message', check=check, timeout=30)
                    choice = int(msg.content) - 1
                    await play(ctx, query=choices[choice])
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to respond")


@client.event
async def on_message(message):
    if message.author == client.user:  # Ignore messages sent by the bot itself
        return

    current_time = time.time()  # Define current_time

    # Check if the message is "helo" and respond with "hi"
    if message.content.lower() == "helo":
        await message.channel.send("hi")
    elif message.content.lower() == "hi":
        await message.channel.send(f"{message.author.mention}, Hii")
    elif message.content.lower() == "hii":
        await message.channel.send(f"{message.author.mention}, Hii")

    # Check if the message contains "bot" and respond with "tu bot"
    # elif "bot" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, ye bot kya laga rakha hai, tumse jada permission hain mare pass chupp chaap raho warna kick maar dunga")
    # elif "love" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, Love you 2 Meri Jaan")
    # elif "noob" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tera pura khandan noob")
    # elif "babu" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, hi babu")
    # elif "betichod" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu betichod")
    # elif "bhosda" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu bsdk")
    # elif "bsdk" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu bsdk")
    # elif "amma" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tumhri amma bahan")
    # elif "MC" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu madharchod")
    # elif "chutiya" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu Chutiya")
    # elif "bkl" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu bkl")
    # elif "pgl" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu pagal")
    # elif "pagal" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu pagal")
    # # elif "hm" in message.content.lower():
    # #     await message.channel.send(f"{message.author.mention}, Hmm Babu")
    # elif "fuck" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, U fucker")
    # elif "bhencho" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu BHENCHO*")
    # elif "chuda" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu chuda*")
    # elif "bc" in message.content.lower():
    #     await message.channel.send(f"{message.author.mention}, tu chuda*")

    # # Define a list of offensive words or phrases
    # offensive_words = ["betichod", "madharchod", "bsdk", "land", "gand", "sale", "bhoosrike", "lauda", "gandu","bhosda", "mc","MC","bc","lodu","wtf","fuck",'Tatti','Baglundi randi','Randi baaj','chutiya','bkl']

    # Check if the message contains any offensive words
    # if any(word in message.content.lower() for word in offensive_words):
    #     try:
    #         await message.delete()
    #     except discord.errors.NotFound:
    #         pass
    #     # Optionally, send a warning to the user
    #     await message.author.send("Gali Diya to Amma Bahan Par aa jaunga 😡")

    # Check for spam based on repeated messages
    user_messages = message_tracker[message.author.id]
    user_messages.append((message.content, current_time))
    
    # Check if the user is spamming
    if len(user_messages) == 5 and user_messages[-1][1] - user_messages[0][1] < 10:  # 10 seconds window
        timeout_duration = user_timeouts[message.author.id]
        await timeout_user(message.guild, message.author, timeout_duration)
        await message.channel.send(f"{message.author.mention} has been timed out for {timeout_duration // 60} minutes for spamming.")
        user_timeouts[message.author.id] = min(timeout_duration * 2, 3600)  # Increase timeout, max 1 hour
        message_tracker[message.author.id].clear()  # Clear the message tracker for the user

    await client.process_commands(message)

async def timeout_user(guild, user, timeout_duration):
    # Get the Timeout role or create it if it doesn't exist
    timeout_role = discord.utils.get(guild.roles, name="Timeout")
    if timeout_role is None:
        timeout_role = await guild.create_role(name="Timeout")

    # Modify channel permissions to restrict the specified user with the Timeout role
    for channel in guild.channels:
        await channel.set_permissions(user, send_messages=False, connect=False)

    # Add the Timeout role to the user
    await user.add_roles(timeout_role)

    # Wait for the specified duration
    await asyncio.sleep(timeout_duration)

    # Remove the Timeout role from the specified user
    await user.remove_roles(timeout_role)

    # Reset channel permissions
    for channel in guild.channels:
        await channel.set_permissions(user, overwrite=None)

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Error: One or more required arguments are missing. Please check your command and try again.")
    else:
        await ctx.send(f"An error occurred: {error}")

@client.command(name='kiss', help='Send a kiss GIF')
async def kiss(ctx, member: discord.Member):
    gif_url = await fetch_gif('kiss')
    if gif_url:
        await ctx.send(f'{ctx.author.mention} kisses {member.mention}! {gif_url}')
    else:
        await ctx.send("Sorry, couldn't fetch the kiss GIF.")

@client.command(name='slap', help='Send a slap GIF')
async def slap(ctx, member: discord.Member):
    gif_url = await fetch_gif('slap')
    if gif_url:
        await ctx.send(f'{ctx.author.mention} slaps {member.mention}! {gif_url}')
    else:
        await ctx.send("Sorry, couldn't fetch the slap GIF.")

@client.command(name='server_info')
async def server_info(ctx):
    server = ctx.guild
    embed = discord.Embed(title="Server Information", color=0x00ff00)
    embed.add_field(name="Server Name", value=server.name, inline=False)
    embed.add_field(name="Server ID", value=server.id, inline=False)
    embed.add_field(name="Members", value=server.member_count, inline=False)
    await ctx.send(embed=embed)

@client.command(name='user_info')
async def user_info(ctx, member: discord.Member):
    if member:
        embed = discord.Embed(title=f"Name: {member.display_name}", color=0x00ff00)
        embed.add_field(name="Username", value=member.name, inline=False)
        embed.add_field(name="User ID", value=member.id, inline=False)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime('%Y-%m-%d'), inline=False)
        
        if member.avatar:
            avatar_url = member.avatar.url
            embed.set_thumbnail(url=avatar_url)
        else:
            default_avatar_url = member.default_avatar.url
            embed.set_thumbnail(url=default_avatar_url)
        
        if len(member.roles) > 1:
            roles_str = ", ".join([role.name for role in member.roles if role.name != '@everyone'])
        else:
            roles_str = "No Role"
        embed.add_field(name="Roles", value=roles_str, inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have permission")

@client.command(name='say')
async def say(ctx, *, message):
    await ctx.send(message)

client.run('MTIxMjI3OTM5ODA1MzcxNTk2OA.Gdp0hT.ig1cLmZQ5mtzAlO0bfNV5liAKdsl8YTeo-xidk')
