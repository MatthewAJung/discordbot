import os
import discord
import random
from discord.ext import commands
from dotenv import load_dotenv
from debtbot import debt
import musicbot
from pretty_help import PrettyHelp
import datetime
from datetime import datetime, timezone, timedelta
import threading

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?',  intents=intents)

names = ['giawsh', 'nuumbsicle', 'christ03', 'thesaltyspoon', 'cowthebilly']
dname = ['josh', 'jonathan', 'chris', 'ryan', 'matthew']

#menu = DefaultMenu('◀️', '▶️', '❌') # You can copy-paste any icons you want.
bot.help_command = PrettyHelp(color=discord.Colour.green(), no_category = 'Commands') 


@bot.event
async def setup_hook():
    with open('cogs.txt', 'r') as file:
        cogs = file.read().split('\n')
        for line in cogs:
            await bot.load_extension(line)

@bot.event	
async def on_ready():
    
    print(f'Logged on as {bot.user}!')

    
    
    # find a guild by name
    for g in bot.guilds:
        if g.id == 585648966683590657:
            bot.anarchy = g
            bot.josh = discord.utils.get(bot.anarchy.text_channels, name='josh')
    #bot.guild = discord.utils.get(bot.guilds, id='yum gyubee')
    #await discord.utils.get(bot.guild.text_channels, name='general').send("ble")
    # make sure to check if it's found
        # find a channel by name


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.guild.id != 585648966683590657:
        return
    if message.author == bot.user:
        return
    if (message.content.lower() == "Hey Nate how's life?".lower() or message.content.lower() == "Hey <@1291233117566275655> how's life?".lower()):
        await message.channel.send("I don’t know, it's alright\nI've been dealin’ with some things like every human being\nAnd really didn't sleep much last night")
    else:
        File_object = open("hi.txt", "r")
        hi_sayings = str(File_object.read()).split('\n')
        for hi in hi_sayings:
            if message.content.lower().startswith(hi.lower()):
                await message.channel.send(hi_sayings[random.randrange(0,len(hi_sayings))])
            File_object.close()
    if (message.content.lower() == "I'm sorry".lower()):
        await message.channel.send("That's fine\nI just think I need a little me time\nI just think I need a little free time\nLittle break from the shows and the bus rides")
    if (message.content.lower() == "Damn".lower()):
        await message.channel.send("It's crazy\nGuess a lot has changed since you last saw me")
    if (message.content.lower() == "idk".lower()):
        await message.channel.send("What they even mean when they're tellin' me I need to come home\nFeels like yesterday I packed the car with everything that I own\nKnow myself less than I know those roads\nBut my hometown no longer feels like home")
    if (message.content.lower() == "?Ego".lower()):
        await message.channel.send("Take away your Ego, because the time will come when I will destroy you in tournaments, yes, maybe not for the first time, but it will come)")
    if (message.content.lower().endswith('a while')):
        await message.channel.send("crocodile")


@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    for i in range(len(names)):
        if after.name == names[i] and before.status != after.status and after.status==discord.Status.online:
            File_object = open("say_online.txt", "r")
            online_sayings = str(File_object.read()).split('\n')
            await bot.josh.send(online_sayings[random.randrange(0,len(online_sayings))].replace('{}',dname[i]))
            File_object.close()

#@bot.command()
#async def findmessage(ctx, id):
    #try:
        #message = await ctx.channel.fetch_message(id)
    #except:
        #return
    #else:
        #await message.reply('Here!', mention_author=False)
    
# @bot.command()
# async def reload(ctx):
# 	"""Reload all cogs"""
# 	with open('cogs.txt', 'r') as file:
        
# 		cogs = file.read().split('\n')
# 		for line in cogs:
# 			print(line)
# 			try:
# 				await bot.reload_extension(line)
# 			except:
# 				await ctx.channel.send("Failure {}".format(line))
# 			else:
# 				await ctx.channel.send("Reloaded {}".format(line))

bot.run(TOKEN)