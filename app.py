from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import discord
from discord.ext import commands
import asyncio
from functools import wraps

app = Flask(__name__)
app.secret_key = 'OwnxejvyhA08pvamFUcC3fUk0vLfAB_4'

# Initialize Discord bot
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

# Store bot instance
bot_instance = {
    'client': client,
    'logs': []
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    guilds = client.guilds
    return render_template('index.html', logs=bot_instance['logs'], guilds=guilds)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'nova' and password == 'hacker':  # Check both username and password
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/control')
@login_required
def control():
    guilds = client.guilds
    return render_template('control.html', guilds=guilds)

@app.route('/guild/<int:guild_id>/channels')
@login_required
def get_channels(guild_id):
    guild = client.get_guild(guild_id)
    if guild:
        channels = [{'id': channel.id, 'name': channel.name} for channel in guild.channels]
        return jsonify(channels)
    return jsonify([])

@client.event
async def on_ready():
    print('Bot is ready.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    bot_instance['logs'].append(f"{message.author}: {message.content}")
    await client.process_commands(message)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    channel_id = request.form['channel_id']
    message = request.form['message']
    channel = client.get_channel(int(channel_id))
    if channel:
        asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)
    return redirect(url_for('control'))

# Define the bot token
BOT_TOKEN = 'MTIxMjI3OTM5ODA1MzcxNTk2OA.Gdp0hT.ig1cLmZQ5mtzAlO0bfNV5liAKdsl8YTeo-xidk'

def run_discord_bot():
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    from threading import Thread
    discord_thread = Thread(target=run_discord_bot)
    discord_thread.start()
    app.run(debug=True)
