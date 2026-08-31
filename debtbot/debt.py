from discord.ext import commands
import json
import datetime
from datetime import datetime, timezone

#Good 
def cents_to_str(val: int):
    if val < 0: 
        return "-" + cents_to_str(-val)
    cents = str(val % 100)
    if len(cents) == 1:
        cents = '0' + cents
    return str(val // 100) + '.' + cents

def addhistory(id, history):
    summary[id]['logs'].append(history)
    if len(summary[id]['logs']) > 20:
        summary[id]['logs'].pop(0)

def getDebt(id,targetid):
    total = 0
    for debt in summary[id]['debts'][targetid]:
        total += summary[id]['debts'][targetid][debt]
    return total
    

def transact(creditor, debitor, amount, reason, ctx):
    timenow = datetime.now()
    time = timenow.isoformat(sep=' ', timespec='minutes')
    his = {'creditor': creditor, 'debitor': debitor, 'amount': amount, 'reason': reason, 'time': time, 'history': []}
    #Create debt
    if creditor not in summary[debitor]['debts']:
        summary[debitor]['debts'][creditor] = {}
    if reason not in summary[debitor]['debts'][creditor]:
        sum = getDebt(debitor, creditor)
        if (sum <= 0 and amount <= 0) or (sum >= 0 and amount >= 0) or amount == 0:
            if amount != 0:
                summary[debitor]['debts'][creditor][reason] = amount
                his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': -amount, 'reason': reason})
                
        else:
            difference = amount
            pop_list = []
            for debt in summary[debitor]['debts'][creditor]:
                surplus = difference + summary[debitor]['debts'][creditor][debt]
                if amount < 0:
                    surplus *= -1
                if surplus >= 0:
                    his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': summary[debitor]['debts'][creditor][debt], 'reason': debt})
                    difference += summary[debitor]['debts'][creditor][debt]
                    pop_list.append(debt)
                else:
                    his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': -difference, 'reason': debt})
                    summary[debitor]['debts'][creditor][debt] += difference
                    difference = 0
                    break
            for debt in pop_list:
                summary[debitor]['debts'][creditor].pop(debt)
            if difference != 0:
                summary[debitor]['debts'][creditor][reason] = difference
                his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': -difference, 'reason': reason})

    else: 
        current = summary[debitor]['debts'][creditor][reason]
        if current > 0 and current + amount <= 0 or current < 0 and current + amount >= 0:
            his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': current, 'reason': reason})
            summary[debitor]['debts'][creditor].pop(reason)
            transact(creditor, debitor, current+amount, reason, ctx)
            his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': -(current + amount), 'reason': reason})
        else:
            summary[debitor]['debts'][creditor][reason] += amount
            his['history'].append({'creditor': creditor, 'debitor': debitor, 'amount': -amount, 'reason': reason})
    return his

def longestPath(node, visited):
    if (node in visited and visited[node]):
        return []
    visited[node] = True
    path = []
    for child in summary[node]['debts']:
        if getDebt(node, child) != 0:
            subpath = longestPath(child, visited)
            if len(subpath) > len(path):
                path = subpath
    path.append(node)
    return path
            

def checkCycles(first, node, visited):
    if (node in visited and visited[node]):
        if node == first:
            return [node]
        else: return []
    visited[node] = True
    cycle = []
    for child in summary[node]['debts']:
        if getDebt(node, child) != 0:
            cycletest = checkCycles(first, child, visited)
            if len(cycletest) > len(cycle):
                cycle = cycletest
    if cycle != []:
        cycle.append(node)
    return cycle

async def cycle(ctx, reason):
    for node in summary:
        visited = {}
        cycles = checkCycles(node, node, visited)
        if len(cycles) > 3:
            cycles.pop()
            lowest = [abs(getDebt(cycles[0], cycles[1])), 0]
            for index in range(0, len(cycles)):
                if abs(getDebt(cycles[index], cycles[(index+1) % len(cycles)])) < lowest[0]:
                    lowest = [abs(getDebt(cycles[index], cycles[(index+1) % len(cycles)])), index]
            change = getDebt(cycles[lowest[1]], cycles[(lowest[1]+1) % len(cycles)])
            for index in range(0, len(cycles)):
                cyclehistory = transact(cycles[(index+1) % len(cycles)], cycles[index], -change, 'Cycle adjustment for {}'.format(reason), ctx)
                cyclehistory['cycle'] = True
                addhistory(cycles[index], cyclehistory)
                cyclehistory = transact(cycles[index], cycles[(index+1) % len(cycles)], +change, 'Cycle adjustment for {}'.format(reason), ctx)
                cyclehistory['cycle'] = True
                addhistory(cycles[(index+1) % len(cycles)], cyclehistory)
                person = ctx.bot.get_user(int(cycles[index]))
                person2 = ctx.bot.get_user(int(cycles[(index+1) % len(cycles)]))
                await ctx.message.channel.send('{} added {} debt to {} for {}'.format(person, -change, person2, '{} Cycle adjustment'.format(reason)))

    
summary = {}     
class Debt(commands.Cog):
    """Commands to for debtbot"""
    def __init__(self, bot):
        self.bot = bot
        with open("debtbot/debt.json",'r') as save:
            summary.update(json.load(save))

    # @commands.command()
    # async def cyclef(self, ctx):
    #     await cycle(ctx)
    #     # for node in summary:
    #     #     visited = {}
    #     #     cycles = checkCycles(node, node, visited)
    #     #     if len(cycles) > 0:
    #     #         print (cycles)
    #     #     if len(cycles) > 3:
    #     #         cycles.pop()
    #     #         lowest = [abs(getDebt(cycles[0], cycles[1])), 0]
    #     #         for index in range(0, len(cycles)):
    #     #             if abs(getDebt(cycles[index], cycles[(index+1) % len(cycles)])) < lowest[0]:
    #     #                 lowest = [abs(getDebt(cycles[index], cycles[(index+1) % len(cycles)])), index]
    #     #         change = getDebt(cycles[lowest[1]], cycles[(lowest[1]+1) % len(cycles)])
    #     #         for index in range(0, len(cycles)):
    #     #             cyclehistory = transact(cycles[(index+1) % len(cycles)], cycles[index], -change, 'Cycle adjustment', ctx)
    #     #             cyclehistory['cycle'] = True
    #     #             addhistory(cycles[index], cyclehistory)
    #     #             cyclehistory = transact(cycles[index], cycles[(index+1) % len(cycles)], +change, 'Cycle adjustment', ctx)
    #     #             cyclehistory['cycle'] = True
    #     #             addhistory(cycles[(index+1) % len(cycles)], cyclehistory)
    #     #             print('{} added {} debt to {} for {}'.format(cycles[index], -change, cycles[(index+1) % len(cycles)], 'Cycle adjustment'))

                    
    #     with open("debtbot/debt.json",'w') as save:    
    #         json.dump(summary, save, indent = 4)
        
    
    # @commands.command()
    # async def load(self, ctx):
    #     global summary
    #     with open("debtbot/debt.json",'r') as save:
    #         summary = json.load(save)

    def netDebt(self, id):
        total = 0
        for target in summary[id]['debts']:
            for debt in summary[id]['debts'][target]:
                total += summary[id]['debts'][target][debt]
        return total

    @commands.command(description='List of your debts and credits')
    async def report(self, ctx):
        """List of your debts and credits"""
        if ctx.guild.id != 585648966683590657:
            return
        authorid = str(ctx.author.id)
        message = 'No transaction history'
        if authorid in summary:
            message = ''
            net = self.netDebt(authorid)
            message += 'Your net debt is **${}**\n'.format(cents_to_str(net))
            title = ['You are owed:\n','You owe:\n','You are owed:\n']
            
            for i in [1,-1]:
                message += title[i]
                if len(summary[authorid]['debts']) == 0:
                    message += 'Nothing lol\n'
                for credits in summary[authorid]['debts']:
                    if getDebt(authorid, credits) * i > 0:
                        target = ctx.bot.get_user(int(credits))
                        message += '**{}**: ${}\n'.format(target.name,cents_to_str(i * getDebt(authorid, credits)))
            
        await ctx.message.channel.send(message)

    @commands.command(desription='Detailed list of your debts and credits')
    async def detailedreport(self, ctx):
        """Detailed list of your debts and credits"""
        if ctx.guild.id != 585648966683590657:
            return
        authorid = str(ctx.author.id)
        message = 'No transaction history'
        if authorid in summary:
            message = ''
            net = self.netDebt(authorid)
            message += 'Your net debt is **${}**\n'.format(cents_to_str(net))
            title = ['You are owed:\n','You owe:\n','You are owed:\n',]
            for i in [1,-1]:
                message += title[i]
                if len(summary[authorid]['debts']) == 0:
                    message += 'Nothing lol\n'
                for credits in summary[authorid]['debts']:
                    if getDebt(authorid, credits) * i > 0:
                        target = ctx.bot.get_user(int(credits))
                        message += '**{}**: ${}\n'.format(target.name,cents_to_str(i * getDebt(authorid, credits)))
                        for reasons in summary[authorid]['debts'][credits]:
                            message += '      ${} for {}\n'.format(cents_to_str(i * summary[authorid]['debts'][credits][reasons]), reasons)
        await ctx.message.channel.send(message)

    @commands.command(description='@users {amount} {reason} - @user1, @user2... owes me ${amount} cuz {reason}')
    async def credit(self, ctx, *args):
        """@users {amount} {reason} - @user1, @user2... owes me ${amount} cuz {reason}"""
        if ctx.guild.id != 585648966683590657:
            return
        if ctx.message.author.id == 363464372703723520:
            await ctx.message.channel.send('hi james')
            return
        authorid = str(ctx.author.id)
        num = 0
        for target in args:
            if (not target.startswith('<@') or not target.endswith('>')):
                break
            if (target[2:-1] == authorid):
                await ctx.message.channel.send("Can't credit yourself")
                return
            num += 1
        if num == 0:
            await ctx.message.channel.send('No mentioned target')
            return
        try:
            amount = int(round(float(args[num]) * 100))
            if amount <= 0:
                await ctx.message.channel.send("Must be positive")
                return
        except:
            await ctx.message.channel.send('Invalid amount')
            return
        if num == len(args)-1:
            await ctx.message.channel.send('No reason given')
            return
        reason = args[num+1]
        for i in range(num+2,len(args)):
                reason += " " + args[i]

        for target in ctx.message.mentions:
            targetid = str(target.id)
            if authorid not in summary:
                summary[authorid] = {'debts': {}, 'logs': []}
            if targetid not in summary:
                summary[targetid] = {'debts': {}, 'logs': []}
            history = transact(targetid, authorid, -int(amount), reason, ctx)
            addhistory(authorid, history)
            history = transact(authorid, targetid, int(amount), reason, ctx)
            addhistory(targetid, history)
            await ctx.channel.send('Credited {} ${} from {} for {}'.format(ctx.author.name,cents_to_str(amount),target.name, reason))

        user = ctx.bot.get_user(int(authorid))
        await cycle(ctx, '{} ({})'.format(reason, user))
        
        with open("debtbot/debt.json",'w') as save:    
            json.dump(summary, save, indent = 4)

    @commands.command()
    async def bill(self, ctx, *args):
        """@users {amount} {reason} - Divides bill amongst users **including** yourself"""
        if ctx.guild.id != 585648966683590657:
            return
        if ctx.message.author.id == 363464372703723520:
            await ctx.message.channel.send('hi james')
            return
        authorid = str(ctx.author.id)
        num = 0
        for target in args:
            if (not target.startswith('<@') or not target.endswith('>')):
                break
            if (target[2:-1] == authorid):
                await ctx.message.channel.send("Can't bill yourself")
                return
            num += 1
        if num == 0:
            await ctx.message.channel.send('No mentioned target')
            return
        try:
            amount = int(round(float(args[num]) * 100))
            if amount <= 0:
                await ctx.message.channel.send("Must be positive")
                return
            amount = int(round(float(amount) / (num+1)))
        except:
            await ctx.message.channel.send('Invalid amount')
            return
        if num == len(args)-1:
            await ctx.message.channel.send('No reason given')
            return
        reason = args[num+1]
        for i in range(num+2,len(args)):
                reason += " " + args[i]

        for target in ctx.message.mentions:
            targetid = str(target.id)
            if authorid not in summary:
                summary[authorid] = {'debts': {}, 'logs': []}
            if targetid not in summary:
                summary[targetid] = {'debts': {}, 'logs': []}
            history = transact(targetid, authorid, -int(amount), reason, ctx)
            addhistory(authorid, history)
            summary[authorid]['group']=True
            history = transact(authorid, targetid, int(amount), reason, ctx)
            addhistory(targetid, history)
            await ctx.channel.send('Credited {} ${} from {} for {}'.format(ctx.author.name,cents_to_str(amount),target.name, reason))
        
        user = ctx.bot.get_user(int(authorid))
        await cycle(ctx, '{} ({})'.format(reason, user))
        with open("debtbot/debt.json",'w') as save:    
            json.dump(summary, save, indent = 4)

    @commands.command(description='@user {amount} - paid off ${amount} to @user')
    async def pay(self, ctx, arg, amount,*,reason=''):
        """@user {amount} - paid off ${amount} to @user"""
        if ctx.guild.id != 585648966683590657:
            return
        if ctx.message.author.id == 363464372703723520:
            await ctx.message.channel.send('hi james')
            return
        authorid = str(ctx.author.id)
        if (arg[2:-1] == authorid):
            await ctx.message.channel.send("Can't pay yourself")
            return
        try:
            amount = int(round(float(amount) * 100))
            if amount <= 0:
                await ctx.message.channel.send("Must be positive")
                return
        except:
            await ctx.message.channel.send('Invalid amount')
            return
        if (not arg.startswith('<@') or not arg.endswith('>')):
            await ctx.message.channel.send("No targets mentioned")
            return
        if len(ctx.message.mentions) > 1:
            await ctx.message.channel.send("Too many targets")
            return
        for target in ctx.message.mentions:
            targetid = str(target.id)
            surplus = int(amount)
            extend = False
            if authorid not in summary:
                summary[authorid] = {'debts': {}, 'logs': []}
            if targetid not in summary:
                summary[targetid] = {'debts': {}, 'logs': []}
            if targetid in summary[authorid]['debts']:
                if reason in summary[authorid]['debts'][targetid]:
                    if summary[authorid]['debts'][targetid][reason] >= 0:
                        surplus -= summary[authorid]['debts'][targetid][reason]
                        if surplus > 0:
                            history = transact(targetid, authorid, -int(summary[authorid]['debts'][targetid][reason]), reason, ctx)
                            history2 = transact(authorid, targetid, -int(summary[targetid]['debts'][authorid][reason]), reason, ctx)
                            extend = True
                        else:
                            history = transact(targetid, authorid, -int(amount), reason, ctx)
                            history2 = transact(authorid, targetid, int(amount), reason, ctx)               
            if surplus > 0:
                historytemp = transact(targetid, authorid, -surplus, 'Overpaid', ctx)
                historytemp2 = transact(authorid, targetid, surplus, 'Overpaid', ctx)
                if extend:
                    history['history'].extend(historytemp['history'])
                    history2['history'].extend(historytemp2['history'])
                else:
                    history = historytemp
                    history2 = historytemp2
            addhistory(authorid, history)
            addhistory(targetid, history2)
            await ctx.channel.send('Paid {} ${}'.format(target.name,cents_to_str(amount)))
        if reason == '':
            p2 = ctx.bot.get_user(int(authorid))
            reason = 'payment by {}'.format(p2)
            await cycle(ctx, reason)
        else:        
            user = ctx.bot.get_user(int(authorid))
            await cycle(ctx, '{} ({})'.format(reason, user))
        
        with open("debtbot/debt.json",'w') as save:
            json.dump(summary, save, indent = 4)

    @commands.command(description='Lists your transaction history')
    async def log(self, ctx):
        """Lists your transaction history"""
        if ctx.guild.id != 585648966683590657:
            return
        if ctx.message.author.id == 363464372703723520:
            await ctx.message.channel.send('hi james')
            return
        if str(ctx.message.author.id) not in summary:
            await ctx.message.channel.send('No debt history')
            return
        s = ''
        cnt = 0
        for idx, log in reversed(list(enumerate(summary[str(ctx.message.author.id)]['logs']))):
            val = log['amount']
            p2 = ctx.bot.get_user(int(log['creditor']))
            reason = log['reason']
            time = log['time']
            if val <= 0:
                s += '{}: Credited $**{}** from **{}** cuz **{}** - {} \n'.format(idx+1,cents_to_str(-val),p2,reason,time)
            if val > 0:
                s += '{}: Debited $**{}** from **{}** cuz **{}** - {} \n'.format(idx+1,cents_to_str(val),p2,reason,time)
            cnt += 1
        if not s:
            s = 'Nothing lol\n'
        while len(s) > 1900:
            await ctx.message.channel.send(s[:1900])
            s = s[1900:]
        await ctx.message.channel.send(s[:-1])
    
    @commands.command(description='Cancel your latest transaction in transaction history')
    async def cancel(self, ctx):
        """Cancel your latest transaction in transaction history (non-cycle adjustment)"""
        if ctx.guild.id != 585648966683590657:
            return
        if ctx.message.author.id == 363464372703723520:
            await ctx.message.channel.send('hi james')
            return
        author = str(ctx.message.author.id)
        idx = len(summary[author]['logs']) -1
        while idx >= 0 and ('cycle' in  summary[author]['logs'][idx]):
            idx-=1
        if len(summary[author]['logs']) < 1:
            await ctx.message.channel.send('Nothing to cancel')
            return
        creditor = summary[author]['logs'][idx]['creditor']
        p2 = ctx.bot.get_user(int(creditor))
        val = summary[author]['logs'][idx]['amount']
        reason = summary[author]['logs'][idx]['reason']
        time = summary[author]['logs'][idx]['time']
        if val <= 0:
            await ctx.message.channel.send("Are you sure you want to cancel this transaction?\n{}: Credited ${} from {} cuz {} - {} \n".format(idx+1,cents_to_str(-val),p2,reason,time))
        if val > 0:
            await ctx.message.channel.send("Are you sure you want to cancel this transaction?\n{}: Debited ${} from {} cuz {} - {} \n".format(idx+1,cents_to_str(val),p2,reason,time))
        def check(m): # checking if it's the same user and channel
            return m.author == ctx.author and m.channel == ctx.channel

        try: # waiting for message
            response = await ctx.bot.wait_for('message', check=check, timeout=20.0) # timeout - how long bot waits for message (in seconds)
        except: # returning after timeout
            await ctx.message.channel.send("Cancel aborted\n")
            return

        # if response is different than yes / y - return
        if response.content.lower() not in ("yes", "y", "yea", "ye", "ya"): # lower() makes everything lowercase to also catch: YeS, YES etc.
            await ctx.message.channel.send("Cancel aborted\n")
            return
        
        for transactions in reversed(summary[author]['logs'][idx]['history']):
            transact(transactions['creditor'], transactions['debitor'], transactions['amount'], transactions['reason'], ctx)
            transact(transactions['debitor'], transactions['creditor'], -transactions['amount'], transactions['reason'], ctx)
        

        for index,logs in enumerate(summary[creditor]['logs']):
            com = summary[author]['logs'][idx]
            if logs['creditor'] == com['debitor'] and logs['debitor'] == com['creditor'] and logs['reason'] == com['reason'] and logs['amount'] == -com['amount'] and logs['time'] == logs['time']:
                summary[creditor]['logs'].pop(index)
        summary[author]['logs'].pop(idx)
        
        user = ctx.bot.get_user(int(author))
        await cycle(ctx, 'cancellation of {} ({})'.format(transactions['reason'], user))
        with open("debtbot/debt.json",'w') as save:
            json.dump(summary, save, indent = 4)
        await ctx.message.channel.send("Cancel successful\n")


async def setup(bot):
    await bot.add_cog(Debt(bot=bot))