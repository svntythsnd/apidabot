import discord
from discord.ext import commands
import json
import re
from os import chdir
import time
chdir('./app')
token = open('D:/slycefolder/ins/pnx/ffck', 'r').read()
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
reactionCheckIDs = set()
class theClient(commands.Bot):
 def __init__(self):
  super().__init__(command_prefix='$ff ', intents=intents)
  self.synced = False
  
 async def on_ready(self):
  await self.wait_until_ready()
  print(f'We have logged in as {self.application_id}')
 
def getDefault(dct, key, default):
 try:
  return dct[key]
 except KeyError:
  return default
 
class Message:
 def __init__(self, content='', embeds=[], files=[], delete_after=None, reference=None, silent=False, mention_author=False):
  self.content = content
  self.embeds = embeds
  self.files = files
  self.delete_after = delete_after
  self.reference = reference
  self.silent = silent
  self.mention_author = mention_author
 @classmethod
 def from_dict(cls, jsonDict):
  content = getDefault(jsonDict, 'content', '')
  embedDict = getDefault(jsonDict, 'embeds', [])
  for e in embedDict:
   if (f := e.get("color")) is not None:
    e.update({"color": int(f, 0)})
   
  embeds = [discord.Embed.from_dict(e) for e in embedDict]
  files = [discord.File(e) for e in getDefault(jsonDict, 'files', [])]
  delete_after = jsonDict.get('delete_after')
  reference = jsonDict.get('reference')
  silent = getDefault(jsonDict, 'silent', False)
  mention_author = getDefault(jsonDict, 'mention_author', False)
  return cls(content, embeds, files, delete_after, reference, silent, mention_author)
 async def send(self, ctx):
  if isAuth(ctx):
   return_message = await ctx.send(content=self.content,embeds=self.embeds,files=self.files,delete_after=self.delete_after,reference=(await ctx.channel.fetch_message(ctx.message.id if r <= 0 else r)if (r := self.reference) is not None else None),silent=self.silent,mention_author=self.mention_author)
   return return_message
  
 async def csend(self, ctx, anonymous=False):
  if anonymous:
   await ctx.message.delete()
   
  return await self.send(ctx)
 
def jsonifyCtx(message):
 jsonStr = message.strip('`').removeprefix('json')
 jsonDict = json.loads(jsonStr)
 return jsonDict
bot = theClient()
isAuth = lambda ctx: not isinstance(ctx.channel, discord.abc.GuildChannel) or ctx.author.guild_permissions.manage_webhooks
async def embedf(ctx, message, anonymous=False):
 await Message.from_dict(jsonifyCtx(message)).csend(ctx, anonymous)
@bot.command()
async def embed(ctx, *, message):
 await embedf(ctx, message)
@bot.command()
async def aembed(ctx, *, message):
 await embedf(ctx, message, True)
async def codeblockf(ctx, message, anonymous=False):
 await Message(f'```{message}```').csend(ctx, anonymous)
@bot.command()
async def codeblock(ctx, *, message):
 await codeblockf(ctx, message)
@bot.command()
async def acodeblock(ctx, *, message):
 await codeblockf(ctx, message, True)
bot.run(token)
