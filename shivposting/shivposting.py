from discord.ext import commands, tasks
import discord
import threading
import json
import datetime
import random
import asyncio
from datetime import datetime, timezone, timedelta, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import matplotlib.dates as mdates
from matplotlib.dates import date2num
from matplotlib.dates import DateFormatter
import numpy as np
import operator

database = {}
class Shivposting(commands.Cog):
    """Commands for shivposting"""
    def __init__(self, bot):
        self.bot = bot
        with open("shivposting/database.json",'r') as save:
            database.update(json.load(save))
        self.names = {'josh': '287621443410460673', 'sean': '249168843036033024', 'chris': '290937643921833984', 'matthew': '371745795608805386', 'isaiah': '282247783170179073', 'ryan': '264955446945644545', 'andrew':'380014221213040644',
                'james': '363464372703723520', 'jonathan': '586748641738489864', 'peter': '260541105865490434', '287621443410460673': 'josh', '249168843036033024':'sean', '290937643921833984':'chris','371745795608805386':'matthew', '282247783170179073':'isaiah', 
                '264955446945644545':'ryan' , '380014221213040644':'andrew','363464372703723520':'james', '586748641738489864':'jonathan','260541105865490434':'peter'}
        self.toobig = {1250610980665167934:1}

    async def getMessage(self, guild_id, channel_id, message_id):
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        return message

    async def getUpvotes(self, message):
        upvotes = {'single': [], 'double': [], 'unique': 0, 'date': message.created_at.isoformat(), 'selfsingle':0, 'selfdouble':0}
        count = {}
        for reaction in message.reactions:
            emoji = 0
            if reaction.emoji == '⏫':
                emoji = 'double'
                emoji2 = 'selfdouble'
            if reaction.emoji == '⬆️' or reaction.emoji == '👍':
                emoji = 'single'
                emoji2 = 'selfsingle'
            if not emoji: continue
            async for user in reaction.users():
                if user.id != message.author.id:
                    count[user.id] = 1
                else: upvotes[emoji2] = 1
                if user.id not in upvotes[emoji]:
                    upvotes[emoji].append(user.id)
        upvotes['unique'] = len(count)
        if str(message.author.id) in database:
            if str(message.id) in database[str(message.author.id)]:
                if 'pin' in database[str(message.author.id)][str(message.id)]:
                    upvotes['pin'] = database[str(message.author.id)][str(message.id)]['pin']
        return upvotes
    
    def getLikes(self, id, daystart, dayend):
        total = {}
        timestamp = datetime.now(timezone.utc)
        for ids in database:
            total[ids] = {'likes': 0,'total':0}
            for messageid in database[ids]:
                date = datetime.fromisoformat(database[ids][messageid]['date'])
                if (timestamp-date).days < daystart and (timestamp-date).days >= dayend:
                    total[ids]['total']+=1
                    if id in database[ids][messageid]['single']:
                        total[ids]['likes']+=1
                    if id in database[ids][messageid]['double']:
                        total[ids]['likes']+=2
        return total

    def countMessage(self, id:str, mid:str):
        return len(database[id][mid]['single']) - database[id][mid]['selfsingle'] + 2* (len(database[id][mid]['double'])-database[id][mid]['selfdouble'])

    def getTotal(self, id, daystart,dayend):
        total = [0,0]
        for messageid in database[id]:
            date = datetime.fromisoformat(database[id][messageid]['date'])
            if (datetime.now(timezone.utc)-date).days < daystart and (datetime.now(timezone.utc)-date).days >= dayend:
                total[0] += len(database[id][messageid]['single']) - database[id][messageid]['selfsingle'] + 2* (len(database[id][messageid]['double'])-database[id][messageid]['selfdouble'])
                total[1] += 1
        return total

    async def getSelf(self, id):
        total = 0
        for messageid in database[id]:
            total += database[id][messageid]['selfsingle'] + 2*database[id][messageid]['selfdouble']
        return total
    
    def getAverageGraph(self, id, days):
        avg = []
        labels = []
        timestamp = datetime.now(timezone.utc)
        for i in range(days, -1, -1):
            total = self.getTotal(str(id), i + 30, i)
        #for i in range(days//30.5, -1, -1):
            #total = self.getTotal(str(id), 30*(i+1), 30*i)
        #for i in range(days, -1, -1):
            #total = self.getTotal(str(id), i+7, i)
        #for i in range(days//30.5, -1, -1):
            #total = self.getTotal(str(id), 7 * (i+1), 7 * i)
            if total[1] != 0:
                avg.append(round(total[0]/total[1], 2))
            else: 
                avg.append(np.nan)
                print('hi')
            labels.append(timestamp - timedelta(days = i))
            #labels.append(timestamp - timedelta(days = 30*i))
            #labels.append(timestamp - timedelta(days = i))
            #labels.append(timestamp - timedelta(days =7* i))
        plt.style.use('dark_background')
        fig, ax = plt.subplots()
        highest = 0
        for val in avg:
            highest = max(val, highest)
        plt.ylim=(0, highest + .2)
       
        loc = mdates.MonthLocator()

        formatter = DateFormatter('%b')
        dates = date2num(labels)
        plt.plot_date(dates, avg, linestyle='-', fmt = '#47a0ff', marker = 'None')
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(formatter)
        ax.yaxis.grid()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        plt.title("{}'s Average Upvotes per Month".format(self.bot.get_user(id)), loc = 'left')
        image = io.BytesIO()
        plt.savefig(image, transparent=True)
        plt.close(fig)
        image.seek(0)
        file = discord.File(image, filename='graph.png')
        return file

    async def getLikeGraph(self, uid, days, days2):
        sid = str(uid)
        #maybe add fields
        labels = []
        num = []
        avg = {}
        labels2 = {}
        total = self.getLikes(uid, 9999, 0)
        for id in database:
            if total[id]['total'] > 0:
                num.append(round(total[id]['likes']/total[id]['total'],2))
                if id in self.names:
                    labels.append(self.names[id])
                else: 
                    user = self.bot.get_user(int(id))
                    labels.append(user.name)
                avg[id] = []
                labels2[id] = []
    
        plt.style.use('dark_background')
        fig, (ax, ax2) = plt.subplots(2, figsize = (9,7))
        highest = 0
        for val in num:
            highest = max(val, highest)

        #'#3A3A3C'
        ax.bar(labels, num, linestyle='-', edgecolor = 'k', color = '#3A3A3C')
        #plt.xticks([],[])
        if sid in self.names:
            name = self.names[sid]
        else: 
            name = self.bot.get_user(uid).name
        ax.set_title("{}'s Like% Distribution".format(name))
        for i in range(len(num)):
            if num[i] != 0:
                ax.text(i,num[i], num[i], va = 'bottom', ha = 'center')
        ax.tick_params("x", labelrotation=90)
        ax.axis('tight')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)


        timestamp = datetime.now(timezone.utc)
        for i in range(days2, -1, -1):
            total = self.getLikes(uid, i + 30, i)
            for blud in avg:
                if total[blud]['total'] > 0:
                    avg[blud].append(total[blud]['likes']/total[blud]['total'])
                else: avg[blud].append(np.nan)
                labels2[blud].append(timestamp - timedelta(days = i))

        loc = mdates.MonthLocator()

        formatter = DateFormatter('%b')
        colour = ['#FF0000', "#FF6A00", '#FFD800','#4CFF00','#00FFFF', '#0094FF', '#0026FF', '#4800FF','#B200FF', '#FF00DC', '#FFFFFF', '#00FF90', '#B6FF00', '#00FF21', '#FF006E']
        count = 0
        for id in avg:
            if id in self.names:
                label = self.names[id]
            else: 
                label = self.bot.get_user(int(id)).name
            dates = date2num(labels2[id])

            ax2.plot_date(dates, avg[id], linestyle='-', fmt = colour[count%len(colour)], marker = 'None', label=label)
            count += 1


        ax2.xaxis.set_major_locator(loc)
        ax2.xaxis.set_major_formatter(formatter)
        ax2.yaxis.grid()
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.set_title("{}'s Average Like% Over Time".format(self.bot.get_user(uid)))
        ax2.legend(loc='upper left')
        fig.tight_layout()
        image = io.BytesIO()
        plt.savefig(image, transparent=True)
        plt.close(fig)
        image.seek(0)
        file = discord.File(image, filename='graph.png')
        return file

    def getDoubleGraph(self, id, days, days2):
        timestamp = datetime.now(timezone.utc)
        sid = str(id)
        #maybe add fields
        num = []
        for meme in database[sid]:
            date = datetime.fromisoformat(database[sid][meme]['date'])
            if timestamp - date <= timedelta(days=days):
                value = len(database[sid][meme]['single']) + len(database[sid][meme]['double']) * 2 - database[sid][meme]['selfsingle'] - database[sid][meme]['selfdouble']*2
                while len(num) - 1 < value:
                    num.append(0)
                num[value] += 1
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, figsize = (9,7))
        
        labels = []
        highest = 0
        for val in num:
            highest = max(val, highest)
        for i in range(len(num)):
            labels.append(str(i))


        #ax1.set_ylim(int(round(highest, 0)) + 2)
        #'#3A3A3C'
        ax1.bar(labels, num, linestyle='-', edgecolor = 'k', color = '#3A3A3C')
        #plt.xticks([],[])
        ax1.set_title("{}'s Post Distribution".format(self.bot.get_user(id)))
        for i in range(len(num)):
            if num[i] != 0:
                ax1.text(i,num[i], num[i], va = 'bottom', ha = 'center')
        #plt.axis('tight')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        #plt.tight_layout()

        avg = []
        labels2 = []
        timestamp = datetime.now(timezone.utc)
        for i in range(days2, -1, -1):
            total = self.getTotal(str(id), i + 30, i)
        #for i in range(days2//30.5, -1, -1):
            #total = self.getTotal(str(id), 30*(i+1), 30*i)
        #for i in range(days2, -1, -1):
            #total = self.getTotal(str(id), i+7, i)
        #for i in range(days2//30.5, -1, -1):
            #total = self.getTotal(str(id), 7 * (i+1), 7 * i)
            if total[1] != 0:
                avg.append(round(total[0]/total[1], 2))
            else: avg.append(np.nan)
            labels2.append(timestamp - timedelta(days = i))
            #labels.append(timestamp - timedelta(days = 30*i))
            #labels.append(timestamp - timedelta(days = i))
            #labels.append(timestamp - timedelta(days =7* i))
        highest = 0
        for val in avg:
            highest = max(val, highest)
        #ax2.set_ylim(highest + 1)
       
        loc = mdates.MonthLocator()

        formatter = DateFormatter('%b')
        dates = date2num(labels2)
        ax2.plot_date(dates, avg, linestyle='-', fmt = '#47a0ff', marker = 'None')
        ax2.xaxis.set_major_locator(loc)
        ax2.xaxis.set_major_formatter(formatter)
        ax2.yaxis.grid()
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.set_title("{}'s Average Upvotes per Month".format(self.bot.get_user(id)))
        fig.tight_layout()
        image = io.BytesIO()
        plt.savefig(image, transparent=True)
        plt.close(fig)
        image.seek(0)
        file = discord.File(image, filename='graph.png')
        return file

    def getTop(self, id):
        top = []
        for meme in database[str(id)]:
            top.append([meme, len(database[str(id)][meme]['single']) - database[str(id)][meme]['selfsingle'] + 2* (len(database[str(id)][meme]['double'])-database[str(id)][meme]['selfdouble'])])
            top = sorted(top, key=lambda x: x[1], reverse=True)
            if len(top) > 3:
                top.pop()
        return top

    async def checkChannel(self, ctx):
        if ctx.channel.id == 1139755718065537094:
            await ctx.channel.send('Please use commands in a different channel (botspam or josh)\n')
            return True
        else: return False


    memeTime = time(hour=23, minute=27) #Create the time on which the task should always run

    async def dupeMessage(self, ctx, mid:str, placement, tie):
        message = await self.getMessage(585648966683590657, 1139755718065537094, int(mid))
        text = '**{}: {}** sent this on {}\n**{}** Total Upvotes, **{}** Unique Upvotes'.format(placement, ctx.bot.get_user(message.author.id),message.created_at.ctime(),self.countMessage(str(message.author.id),mid), database[str(message.author.id)][mid]['unique'])
        if tie:
            text += ' **(Tied with {} others)**'.format(tie-1)
        text += '\n{}\n'.format(message.jump_url)
        print(mid)
        if message.id in self.toobig:
            await ctx.channel.send(text + 'File too big click link to see\n')
        elif len(message.embeds) > 0:
            await ctx.channel.send(text + message.content)
        else:
            await ctx.channel.send(text + message.content, files = [await m.to_file() for m in message.attachments])

    async def archiveMessage(self, message):
        channel = self.bot.anarchy.get_channel(1388255110295060510)
        text = '**{}** sent this on {}\n**{}** Total Upvotes, **{}** Unique Upvotes'.format(self.bot.get_user(message.author.id),message.created_at.ctime(),self.countMessage(str(message.author.id),str(message.id)), database[str(message.author.id)][str(message.id)]['unique'])
        text += '\n{}\n'.format(message.jump_url)
        if message.id in self.toobig:
            mes = await channel.send(text + 'File too big click link to see\n')
        elif len(message.embeds) > 0:
            mes =await channel.send(text + message.content)
        else:
            mes=await channel.send(text + message.content, files = [await m.to_file() for m in message.attachments])
        return mes

    @tasks.loop(time = memeTime) #Create the task
    async def newMeme(self):
        if datetime.now(timezone.utc).weekday() != 4:
            return
        channel = self.bot.anarchy.get_channel(1388255110295060510)
        ran = random.random()
        lib = []
        for id in database:
            for mid in database[id]:
                date = datetime.fromisoformat(database[id][mid]['date'])
                timestamp = datetime.now(timezone.utc)
                if database[id][mid]['unique'] >= 4 and (timestamp - date).days <7:
                    lib.append(mid)
        total = len(lib) -1
        num = round(ran*total)
        if len(lib) > 0:
            message = await self.getMessage(585648966683590657, 1139755718065537094, int(lib[num]))
            text = '**Meme of the Week**\nSent by **{}** on {}\n{}\n'.format(self.bot.get_user(message.author.id),message.created_at.ctime(),'https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(lib[num]))
            print(mid+ ' from newMeme')
            if len(message.embeds) > 0:
                await channel.send(text + message.content)
            else:
                await channel.send(text + message.content, files = [await m.to_file() for m in message.attachments])
            return
        else:
            await channel.send('**Meme of the Week**\n\n\nno one was funny this week lol')

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.newMeme.start()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if payload.guild_id != 585648966683590657:
            return
        if self.bot.get_channel(payload.channel_id).name != 'shivposting':
            return
        message = await self.getMessage(payload.guild_id, payload.channel_id, payload.message_id)
        if message.author.id == 1291233117566275655 or message.author.id == 1211781489931452447:
            return
        #guild = self.bot.get_guild(payload.guild_id)
        #channel = guild.get_channel(payload.channel_id)
        #message = await channel.fetch_message(payload.message_id)
        authorid = str(message.author.id)
        messageid = str(message.id)
        if authorid not in database:
            database[authorid] = {}
        database[authorid][messageid] = await self.getUpvotes(message)
        if database[authorid][messageid]['unique'] >= 5: 
            if 'pin' in database[authorid][messageid]:
                channel = self.bot.anarchy.get_channel(1388255110295060510)
                mes = await self.getMessage(585648966683590657, 1388255110295060510, database[authorid][messageid]['pin'])
                text = '**{}** sent this on {}\n**{}** Total Upvotes, **{}** Unique Upvotes'.format(self.bot.get_user(message.author.id),message.created_at.ctime(),self.countMessage(str(message.author.id),str(message.id)), database[str(message.author.id)][str(message.id)]['unique'])
                text += '\n{}\n'.format(message.jump_url)
                await mes.edit(content =text + message.content)
            else:
                mes = await self.archiveMessage(message)
            
                database[authorid][messageid]['pin'] = mes.id
            

        if database[str(message.author.id)][str(message.id)]['unique'] == 0 and database[str(message.author.id)][str(message.id)]['selfsingle'] == 0 and database[str(message.author.id)][str(message.id)]['selfdouble'] == 0 and not message.embeds and not message.attachments: 
            del database[str(message.author.id)][str(message.id)]
        with open("shivposting/database.json",'w') as save:    
            json.dump(database, save, indent = 4)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id != 585648966683590657:
            return
        if self.bot.get_channel(payload.channel_id).name != 'shivposting':
            return
        
        
        message = await self.getMessage(payload.guild_id, payload.channel_id, payload.message_id)
        if message.author.id == 1291233117566275655 or message.author.id == 1211781489931452447:
            return
        authorid = str(message.author.id)
        messageid = str(message.id)
        if authorid not in database:
            database[authorid] = {}
        database[authorid][messageid] = await self.getUpvotes(message)
        if 'pin' in database[authorid][messageid]:
            if database[authorid][messageid]['unique'] < 5:
                mes = await self.getMessage(585648966683590657, 1388255110295060510, database[authorid][messageid]['pin'])
                await mes.delete()
                del database[authorid][messageid]['pin']
            else:
                mes = await self.getMessage(585648966683590657, 1388255110295060510, database[authorid][messageid]['pin'])
                text = '**{}** sent this on {}\n**{}** Total Upvotes, **{}** Unique Upvotes'.format(self.bot.get_user(message.author.id),message.created_at.ctime(),self.countMessage(str(message.author.id),str(message.id)), database[str(message.author.id)][str(message.id)]['unique'])
                text += '\n{}\n'.format(message.jump_url)
                await mes.edit(content= text + message.content)

        if database[authorid][messageid]['unique'] == 0 and database[authorid][messageid]['selfsingle'] == 0 and database[authorid][messageid]['selfdouble'] == 0 and not message.embeds and not message.attachments: 
            del database[authorid][messageid]
        with open("shivposting/database.json",'w') as save:    
            json.dump(database, save, indent = 4)
               
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != 585648966683590657:
            return
        if message.author.id == 1291233117566275655 or message.author.id == 1211781489931452447:
            return
        threading.Event().wait(0.0001)
        if (message.embeds or message.attachments) and message.channel.name == 'shivposting':
            if str(message.author.id) not in database:
                database[str(message.author.id)] = {}
            database[str(message.author.id)][str(message.id)] = await self.getUpvotes(message)

            with open("shivposting/database.json",'w') as save:    
                json.dump(database, save, indent = 4)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id != 585648966683590657:
            return
        for id in database:
            if str(payload.message_id) in database[id]:
                del database[id][str(payload.message_id)]
        with open("shivposting/database.json",'w') as save:    
            json.dump(database, save, indent = 4)
        
#    @commands.command()
#    async def grabhistory(self, ctx, *value):
#        total = 0
#        if value and value[0].isdigit(): 
#            total = 1
#            num = int(value[0])
#        global database
#        database = {}
#        if ctx.message.author.id != 371745795608805386:
#            return
#        counter = 0
#        channel = self.bot.anarchy.get_channel(1139755718065537094)
#        async for note in channel.history(limit = 99999, oldest_first = True):
#            if total and counter%(num//10) == 0:
#                print('Completed {}%'.format(round(counter/num * 100)))
                #await ctx.channel.send('Completed {}%'.format(round(counter/num * 100)))
            #if note.pinned:
                #await note.unpin()
#            if note.embeds or note.attachments or any([lambda x : x.emoji == '⏫' or x.emoji == '⬆️' or x.emoji == '👍' for x in note.reactions]):
#                if note.author.id == 1291233117566275655:
#                    continue
#                if str(note.author.id) not in database:
#                    database[str(note.author.id)] = {}
#                database[str(note.author.id)][str(note.id)] = await self.getUpvotes(note) 
#                if database[str(note.author.id)][str(note.id)]['unique'] >= 5:
#                    #await note.pin()
#                    print(note.id)
#                    mes = await self.archiveMessage(note)
#                    database[str(note.author.id)][str(note.id)]['pin'] = mes.id
#                if database[str(note.author.id)][str(note.id)]['unique'] == 0 and database[str(note.author.id)][str(note.id)]['selfsingle'] == 0 and database[str(note.author.id)][str(note.id)]['selfdouble'] == 0 and not note.embeds and not note.attachments: 
#                    del database[str(note.author.id)][str(note.id)]


#            with open("shivposting/database.json",'w') as save:
#                json.dump(database, save, indent = 4)   
#            counter += 1
#        await ctx.channel.send('Done!')

 #       if database[authorid][messageid]['unique'] >= 5: 
 #           mes = await self.archiveMessage(message)
 #           
 #           database[authorid][messageid]['pin'] = mes.id

#        with open("shivposting/database.json",'w') as save:    
#            json.dump(database, save, indent = 4)   

    @commands.command()
    async def poststats(self, ctx):
        if ctx.guild.id != 585648966683590657:
            return
        if await self.checkChannel(ctx):
            return
        threemonths = self.getTotal(str(ctx.author.id), 91,0)
        sixmonths = self.getTotal(str(ctx.author.id), 183,0)
        year = self.getTotal(str(ctx.author.id), 365,0)
        alltime =self.getTotal(str(ctx.author.id),99999,0)
        text = '**Average Upvotes Per Post (Double Upvote Counts as 2):**\n'
        text += 'Last 3 Months: **{}**\nLast 6 Months: **{}**\nLast Year: **{}**\nAll Time: **{}**\n'.format(round(threemonths[0]/threemonths[1],2),round(sixmonths[0]/sixmonths[1],2),round(year[0]/year[1],2), round(alltime[0]/alltime[1],2))
        #file = self.getGraph(ctx.author.id, 9999)
        file = self.getDoubleGraph(ctx.author.id, 9999, 365)
        await ctx.channel.send(content=text, file=file )

    @commands.command()
    async def likestats(self, ctx, *arg):
        if ctx.guild.id != 585648966683590657:
            return
        if await self.checkChannel(ctx):
            return
        if not arg: id = ctx.author.id
        else: id = int(arg[0])

        file = await self.getLikeGraph(id, 9999, 365)
        text = '\n'
        await ctx.channel.send(text,file=file)

    @commands.command()
    async def summary(self, ctx, *id):
        if ctx.guild.id != 585648966683590657:
            return
        if await self.checkChannel(ctx):
            return
        text = ''

        if not id:
            #file1 = self.getGraph(ctx.author.id, 9999)
            file = self.getDoubleGraph(ctx.author.id, 9999, 365)
            text += "{}'s top posts are:\n".format(ctx.bot.get_user(ctx.author.id))
            top = self.getTop(ctx.author.id)
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[0][1], top[0][0])
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[1][1], top[1][0])
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[2][1], top[2][0])
            #file2 = self.getAverageGraph(ctx.author.id, 365)
        else: 
            #file1 = self.getDoubleGraph(int(id[0]), 9999)
            file = self.getDoubleGraph(int(id[0]), 9999, 365)
            text += "{}'s top posts are:\n".format(ctx.bot.get_user(int(id[0])))
            top = self.getTop(int(id[0]))
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[0][1], top[0][0])
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[1][1], top[1][0])
            text += '{} Upvotes: https://discord.com/channels/585648966683590657/1139755718065537094/{}\n'.format(top[2][1], top[2][0])
            #file1 = self.getAverageGraph(int(id[0]), 365)
        #await ctx.channel.send(text,files = [file1, file2])
        await ctx.channel.send(text,file=file)
    
    def getOperator(self, par):
        ops1={'>=': operator.ge, '<=': operator.le}
        ops2 = {'>': operator.gt, '<': operator.lt, '=': operator.eq}
        
        if par[:2] in ops1:
            if par[2:].isdigit():
                return {'op': ops1[par[:2]], 'num': int(par[2:])}
            else: return None
        elif par[:1] in ops2:
            if par[1:].isdigit():
                return {'op': ops2[par[:1]], 'num': int(par[1:])}
            else: return None
        else: return None

    @commands.command()
    async def random(self, ctx, *par):
        """Operator Format: [u] | OPERATOR | NUM
        u (optional): Uses # of unique upvoters (default: total # of upvotes)
        OPERATOR: {<, <=, =, >=, >}
        NUM: Number of upvotes
        Any number of operators can be used **e.g. ?random >=8 u<6**"""
        if ctx.guild.id != 585648966683590657:
            return
        ran = random.random()
        op1 = []
        op2 = []
        if len(par) == 0:
            op1.append({'op': operator.ge, 'num': 4})
        for i in range(len(par)):
            if par[i].startswith('u'):
                temp = self.getOperator(par[i][1:])
                if temp == None:
                    await ctx.channel('Error: Invalid Arguments\n')
                    return
                else: op2.append(temp)
            else:
                temp = self.getOperator(par[i])
                if temp == None:
                    await ctx.channel('Error: Invalid Arguments\n')
                    return
                else: op1.append(temp)
        
        subset = []
        for id in database:
            for mid in database[id]:
                skip = False
                for item in op1:
                    if not item['op'](self.countMessage(id, mid), item['num']):
                        skip = True
                for item in op2:
                    if not item['op'](database[id][mid]['unique'], item['num']):
                        skip = True
                if not skip:
                    subset.append(mid)
        
        if len(subset) == 0:
            await ctx.channel.send('Error: No Messages Match Criteria\n')
            return
        index = round(ran*len(subset))%len(subset)
        mid = subset[index]
        message = await self.getMessage(585648966683590657, 1139755718065537094, int(subset[index]))
        text = '**{}** sent this on {}\n**{}** Total Upvotes, **{}** Unique Upvotes\n{}\n'.format(ctx.bot.get_user(message.author.id),message.created_at.ctime(),self.countMessage(str(message.author.id),mid), database[str(message.author.id)][mid]['unique'], message.jump_url)
        print(subset[index])
        if message.id in self.toobig:
            await ctx.channel.send(text + 'File too big click link to see\n')
        elif len(message.embeds) > 0:
            await ctx.channel.send(text + message.content)
        else:
            await ctx.channel.send(text + message.content, files = [await m.to_file() for m in message.attachments])



    @commands.command()
    async def shivleaderboard(self, ctx, *args):
        if ctx.guild.id != 585648966683590657:
            return
        if await self.checkChannel(ctx):
            return
        number = 5
        if args and args[0].isdigit():
            number = int(args[0])
        top = []
        lowest = 0
        tie = []
        for id in database:
            for mid in database[id]:
                num = self.countMessage(id, mid)
                if len(top) >= number:
                    if lowest < num:
                        top.append({'mid': mid,'num': num})
                        top = sorted(top, key=lambda item: item['num'], reverse=True)
                        top.pop()
                        if lowest != top[number-1]['num']:
                            tie.clear()
                            lowest = top[number-1]['num']
                            for meme in top:
                                if meme['num'] == lowest:
                                    tie.append(meme['mid'])
                    elif lowest == num:
                        tie.append(mid)
                else: 
                    top.append({'mid': mid, 'num': num})
                    top = sorted(top, key=lambda item: item['num'], reverse = True)
                    tie.clear()
                    lowest = top[len(top)-1]['num']
                    for meme in top:
                        if meme['num'] == lowest:
                            tie.append(meme['mid'])
        count = 0
        for meme in top:
            if meme['num'] == lowest:
                count+=1
        if count < len(tie):
            end = number-count

        used = {}
        for i in range(end):
            await self.dupeMessage(ctx, top[i]['mid'], i+1, 0)
        for i in range(count):
            while True:
                ran = random.random()
                tieCount = len(tie)
                index = round(ran*tieCount)%tieCount
                if index not in used:
                    used[index] = 1
                    break
            await self.dupeMessage(ctx, tie[index], i+1+end, tieCount)





async def setup(bot):
    await bot.add_cog(Shivposting(bot=bot))