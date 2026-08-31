import discord
from discord.ext import commands
import json
import datetime
from datetime import datetime, timezone, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import matplotlib.dates as mdates
from matplotlib.dates import date2num
from matplotlib.dates import DateFormatter
import numpy as np

stats = {}     
def get_avg(id, ex, daystart, dayend, guild):
    count = 0
    total = 0
    empty = True
    if id not in stats[guild]:
        return None
    timestamp = datetime.now(timezone.utc)
    for wordle in stats[guild][id]['log']:
        date = datetime.fromisoformat(wordle[0]) 

        if (timestamp - date).days < daystart and (timestamp-date).days >= dayend:
            if str(wordle[1]).isdigit():
                total += wordle[1]
                count += 1
            elif ex:
                total += 7
                count += 1
            empty = False
    
    return [total, count, empty]

class Wordle(commands.Cog):
    """Commands for wordle bot"""
    def __init__(self, bot):
        self.bot = bot
        self.channel = {}
        with open ("wordle/servers.json",'r') as save:
            self.channel.update(json.load(save))
        for guild in self.channel:
            with open("wordle/{}stats.json".format(guild),'r') as save:
                stats[guild] = {}
                stats[guild].update(json.load(save))

    def getGraph(self, id, days, guild):
        timestamp = datetime.now(timezone.utc)
        embed = discord.Embed( timestamp=timestamp)
        #maybe add fields
        labels = ['X','6','5','4', '3','2', '1']
        dictionary = {  'X':0, 6:1,  5:2,  4:3, 3:4, 2:5,1: 6}
        num = [0, 0, 0, 0, 0, 0, 0]
        for wordle in stats[guild][str(id)]['log']:
            date = datetime.fromisoformat(wordle[0])
            if timestamp - date <= timedelta(days=days):
                num[dictionary[wordle[1]]] += 1
        plt.style.use('dark_background')

        first = '9999-98-76'
        for wordle in stats[guild][str(id)]['log']:
            if int(wordle[0][:4]) < int(first[:4]):
                if int(wordle[0][5:7]) < int(first[5:7]):
                    if int(wordle[0][8:10]) < int(first[8:10]):
                        first = wordle[0]
        fig, (ax, ax2) = plt.subplots(2)

        ax.barh(labels, num, linestyle='-', edgecolor = 'k', color = '#538D4E')
        ax.set_xticks([],[])
        ax.set_title("{}'s Guess Distribution".format(self.bot.get_user(id)))
        for i in range(len(num)):
            if num[i] != 0:
                ax.text(num[i]-.5,i, num[i], va = 'center', ha = 'right')
        #plt.axis('tight')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

        avg = []
        labels2 = []
        for i in range((timestamp-datetime.fromisoformat(first)).days, -1, -1):
            average = get_avg(str(id), True, i + 7, i, guild)
            if average[2] == False:
                avg.append(round(average[0]/average[1],2))
            else: avg.append(np.nan)
            labels2.append(timestamp - timedelta(days = i))
        #ax2.set_ylim(highest + 1)

        if (timestamp-datetime.fromisoformat(first)).days <= 60:
            loc = mdates.WeekdayLocator()
        else:
            loc = mdates.MonthLocator()


        formatter = DateFormatter('%d %b')
        dates = date2num(labels2)
        ax2.plot_date(dates, avg, linestyle='-', fmt = '#47a0ff', marker = 'None')
        ax2.xaxis.set_major_locator(loc)
        ax2.xaxis.set_major_formatter(formatter)
        ax2.yaxis.grid()
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.set_title("{}'s Wordle Rolling Average".format(self.bot.get_user(id)))

        fig.tight_layout()

        image = io.BytesIO()
        plt.savefig(image, transparent=True)
        plt.close(fig)
        image.seek(0)
        file = discord.File(image, filename = 'graph.png')
        embed.set_image(url = 'attachment://graph.png')
        return [file, embed]

    @commands.command()
    async def setchannel(self,ctx):
        """Sets channel to be tracked for Wordle stats"""
        guild = str(ctx.guild.id)
        self.channel[guild] = str(ctx.channel.id)
        if not ctx.author.guild_permissions.administrator:
            await ctx.channel.send('You do not have permission to run this command')
            return
        if guild not in stats:
            stats[guild] = {}
        with open("wordle/{}stats.json".format(guild), "w") as save:
            json.dump(stats[guild], save, indent = 4)

        with open("wordle/servers.json",'w') as save:    
            json.dump(self.channel, save, indent = 4)

        await ctx.channel.send ('This channel will now be tracked for Wordle stats')
                        


    def logStats(self, id, guild, date, guesses):
        if id not in stats[guild]:
            stats[guild][id] = {'log': [], 'streak': {'current':0, 'max':0}}
        stats[guild][id]['log'].append([date.isoformat(), guesses])

    def logStreak(self,id,guild,guesses):
        if id not in stats[guild]:
            return ""
        if isinstance(guesses, int) and guesses <= 3 and guesses > 0:
            stats[guild][id]['streak']['current'] += 1

            if stats[guild][id]['streak']['max'] < stats[guild][id]['streak']['current']:
                stats[guild][id]['streak']['max'] = stats[guild][id]['streak']['current']
                if stats[guild][id]['streak']['current'] >= 2:
                    return "{} has a {} day streak of <= 3 guesses, their new highest streak!\n".format(self.bot.get_user(int(id)).display_name, stats[guild][id]['streak']['current'])
            elif stats[guild][id]['streak']['current'] >= 2: return "{} has a {} day streak of <= 3 guesses!\n".format(self.bot.get_user(int(id)).display_name, stats[guild][id]['streak']['current']) 
        else: 
            cur = stats[guild][id]['streak']['current']
            stats[guild][id]['streak']['current'] = 0
            if cur >= 2:
                return "{} has lost their {} day streak :(\n".format(self.bot.get_user(int(id)).display_name, cur)
        return ""
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Message filter
        guild = str(message.guild.id)
        channel = str(message.channel.id)
        #371745795608805386
        #1211781489931452447
        if guild not in self.channel or channel != self.channel[guild] or message.author.id != 1211781489931452447  or not message.content.startswith('**Your group is on a'): return
        
        # Variables needed
        date = message.created_at
        date += timedelta(days=-1)
        guild = str(message.guild.id)

        text = message.content

        index = {'1/6:': 1,'2/6:': 2,'3/6:': 3,'4/6:': 4,'5/6:': 5,'6/6:': 6,'X/6:': 'X'}
        idindex = {}
        check = ['`','!',':','-', '#','*', '(', ')', '_', '+', '{', '}', '[', ']', '\\', ',','.']
        for user in message.guild.members:
            displayname = user.display_name
            cursor = 0
            while cursor < len(displayname):
                if displayname[cursor] in check:
                    displayname = displayname[0:cursor] + '\\' + displayname[cursor:len(displayname)]
                    cursor += 1
                cursor += 1
            idindex[displayname] = str(user.id)
        used = []
        cursor = 0
        finalmessage = ""

        # Scrub through entire message
        while cursor < len(message.content)-3:
            if text[cursor:cursor+4] in index:
                guesses = index[text[cursor:cursor+4]]
                while True:
                    if cursor == len(text) or text[cursor] == '\n':
                        break   
                    elif text[cursor:cursor+2] == '<@':
                        cursor += 2
                        temp = cursor
                        while text[temp] != '>':
                            temp+=1
                        id = text[cursor:temp]
                        used.append(id)
                        self.logStats(id, guild, date, guesses)
                        finalmessage += self.logStreak(id, guild, guesses)
                        cursor = temp
                    elif text[cursor] == '@':
                        cursor+=1
                        for i in range(len(text),cursor,-1):
                            if text[cursor:i] in idindex:
                                id = idindex[text[cursor:i]]
                                used.append(id)
                                self.logStats(id, guild, date, guesses)
                                finalmessage += self.logStreak(id, guild, guesses)
                                cursor = i-1
                    cursor += 1
            cursor += 1

        await message.add_reaction('👍')

        for id in stats[guild]:
            if id not in used:
                finalmessage += self.logStreak(id,guild,0)
        if finalmessage != "":
            await message.channel.send(finalmessage)

        with open("wordle/{}stats.json".format(guild),'w') as save:    
            json.dump(stats[guild], save, indent = 4)

    @commands.command()
    async def streaks(self, ctx):
        lb = []
        guild = str(ctx.guild.id)
        if guild not in stats:
            await ctx.channel.send("This server has not set up Wordle tracking")
            return
        text = 'You have a current streak of {}\n'.format(stats[guild][str(ctx.author.id)]['streak']['current'])
        for id in stats[guild]:
            if stats[guild][id]['streak']['max'] >= 1:
                lb.append([id, stats[guild][id]['streak']['max']])
        lb = sorted(lb, key=lambda avg: avg[1], reverse = True) 
        text += '**Leaderboard of Streaks (<= 3 Guesses)**\n'
        for i in range(len(lb)):
            text += '**{}:** {} with **{}**\n'.format(i+1, ctx.bot.get_user(int(lb[i][0])).display_name, lb[i][1])
        if len(lb) < 1: text += 'No user has a max streak >= 3\n'
        await ctx.message.channel.send(text)

    @commands.command()
    async def wordlestats(self, ctx, *args):
        """Returns Wordle stats such as distribution, total average, and rolling average"""
        if not args:
            id = ctx.author.id
        else: id = int(args[0])
        
        guild = str(ctx.guild.id)
        if guild not in stats:
            await ctx.channel.send("This server has not set up Wordle tracking")
            return
        
        if str(id) not in stats[guild] or len(stats[guild][str(id)]['log']) <1:
            await ctx.channel.send('You do not have any stats')
            return
        
        count1 = get_avg(str(id), False, 9999, 0, str(ctx.guild.id))
        count2 = get_avg(str(id), True, 9999, 0, str(ctx.guild.id))
        if count1 == None or count1[1] == 0:
            avg1 = 'N/A'
        else: avg1 = round(count1[0]/count1[1],3)
        if count2 == None or count2[1] == 0:
            avg2 = 'N/A'
        else: avg2 = round(count2[0]/count2[1],3)

        graph = self.getGraph(id, 9999, str(ctx.guild.id))
        await ctx.message.channel.send("Your average non failed attempts is **{}**.\nYour average attempts with failed counting as 7 is **{}**".format(avg1, avg2), file = graph[0])

    @commands.command()
    async def leaderboard(self, ctx):
        """Provides server leaderboard of Wordle averages"""
        lb1 = []
        lb2 = []

        guild = str(ctx.guild.id)
        if guild not in stats:
            await ctx.channel.send("This server has not set up Wordle tracking")
            return
        for id in stats[guild]:
            if len(stats[guild][id]['log']) >= 1 and ctx.bot.get_user(int(id)):
                count1 = get_avg(id, False, 9999, 0, str(ctx.guild.id))
                count2 = get_avg(id, True, 9999, 0, str(ctx.guild.id))
                if count1[1] > 0:
                    lb1.append([id, round(count1[0]/count1[1],3)])
                if count2[1] > 0:
                    lb2.append([id, round(count2[0]/count2[1],3)])
        lb1 = sorted(lb1, key=lambda avg: avg[1]) 
        lb2 = sorted(lb2, key=lambda avg: avg[1]) 
        text = '**Leaderboard for non failed attempts average:**\n'
        for i in range(len(lb1)):
            
            text += '**{}:** {} with **{}**\n'.format(i+1, ctx.bot.get_user(int(lb1[i][0])).display_name, lb1[i][1])
        if len(lb1) < 1: text += 'No user has >= 1 tracked Wordle attempts\n'
        text += '\n**Leaderboard for all attempts (failed=7) average:**\n'
        for i in range(len(lb2)):
            text += '**{}:** {} with **{}**\n'.format(i+1, ctx.bot.get_user(int(lb2[i][0])).display_name, lb2[i][1])
        if len(lb2) < 1: text += 'No user has >= 1 tracked Wordle attempts\n'
        await ctx.message.channel.send(text)

    
async def setup(bot):
    await bot.add_cog(Wordle(bot=bot))