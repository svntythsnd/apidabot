import time
import datetime
import requests
import io
import discord
import json
import re
from discord.ext import commands, tasks
from os import chdir
chdir('./app')
class InfoMsg:
 permission_error = 'Interaction failed - you might not have the required permissions'
 member_presence_error = 'User is not on this server!'
 member_unverifiable_error = 'User is not manually verifiable!'
 force_verification_success = lambda id: f'<@{id}> has been force-verified!'
 verification_success = lambda id: f'<@{id}> has been verified!'
 verification_declined_success = lambda id: f'<@{id}> has been rejected and kicked!'
 verification_declined_audit = 'Verification attempt was declined by staff'
 verification_period_expiration_audit = 'Verification period expired'
 manual_verification_period_expiration_audit = 'Manual verification period expired'
 verification_denied = 'Your verification request was denied by the system. You may have already submitted your request'
 verification_accepted = 'Your verification request has been submitted!'
 force_verification_success_audit = 'Verification forced'
 verification_role_on_join_audit = 'Unverified role given to new member'
 set_unverified_role = lambda id: f'Unverified role set to <@&{id}>'
 set_v_timeout = lambda seconds: f'Verification timeout interval set to {datetime.timedelta(seconds=seconds)}'
 set_mv_timeout = lambda seconds: f'Manual verification timeout interval set to {datetime.timedelta(seconds=seconds)}'
 set_v_message = lambda json: f'Verification message set to:\n```json\n{json}```'
 set_vlog_message = lambda json: f'Verification log message template set to:\n```json\n{json}```'
 set_vlog_channel = lambda id: f'Verification log channel set to <#{id}>'
path = 'external.json'
token = open('D:/slycefolder/ins/pnx/apd', 'r').read()
def jsonPrettify(jsonStr, sort_keys: bool = False, indent: int = 4):
 return json.dumps(safeload(jsonStr),sort_keys=sort_keys, indent=indent)
class TimeUnits:
 second = 1
 minute = 60*second
 hour = 60*minute
 day = 24*hour
 week = 7*day
 unit_dict = {'s': second, 'm': minute, 'h': hour, 'd': day, 'w': week}
 unit_map = lambda unit: TimeUnits.unit_dict.get(unit)
intents = discord.Intents(message_content = True,guilds = True,members = True,)
def safeload(string):
 try : return json.loads(string)
 except json.JSONDecodeError : return {}
def filter_none(dt):
 filtered_dt = {}
 for k, v in dt.items():
  if any([v in [[],{},None,''],(k in ['mention_author']) == v]): continue
  if isinstance(v, dict): v = filter_none(v)
  elif isinstance(v, list): v = [filter_none(e) for e in v]
  filtered_dt.update({k: v})
 return filtered_dt
class theClient(commands.Bot):
 def __init__(self):
  super().__init__(intents=intents)
  self.synced = False
  
 async def on_ready(self):
  await self.wait_until_ready()
  print(f'We have logged in as {self.application_id}')
  print('\n'.join([f"{(guild := self.get_guild(gid)).name}:\n{',\n'.join(str(e) for e in await guild.invites())}" for gid in ext.guilds.getids()]))
  usercheck_task.start()
 async def usercheck(self):
  newguilds = {}
  for gid in ext.guilds.getids():
   guild = ext.guilds.getg(gid)
   rguild = self.get_guild(gid)
   new_verif_pending = []
   for user in guild.verif_pending:
    if ruser := rguild.get_member(user.id):
     if time.time() - user.created_at < guild.verif_timeout:
      new_verif_pending.append(user)
     else:
      await rguild.kick(ruser, reason=InfoMsg.verification_period_expiration_audit)
     
    
   guild.verif_pending = new_verif_pending
   new_verif_admin_pending = []
   for user in guild.verif_admin_pending:
    if ruser := rguild.get_member(user.id):
     if time.time() - user.created_at < guild.verif_admin_timeout:
      new_verif_admin_pending.append(user)
     else:
      await rguild.kick(ruser, reason=InfoMsg.manual_verification_period_expiration_audit)
     
    
   guild.verif_admin_pending = new_verif_admin_pending
   newguilds.update({str(gid): guild.dictify()})
  ext.guilds = GuildCache(newguilds)
 
def getDefault(dct, key, default):
 try : return dct[key]
 except KeyError : return default
class Ext:
 @property
 def guilds(self):
  with open(path, 'r') as f : return GuildCache(getDefault(safeload(f.read()), 'guilds', {}))
 @guilds.setter
 def guilds(self, new):
  with open(path, 'r') as f:
   extDict = safeload(f.read())
   extDict.update({'guilds': new.getall()})
  with open(path, 'w') as f: f.write(json.dumps(extDict, indent=4))
 
class GuildCache:
 def __init__(self, v: dict): self._v = {i: CachedGuild(i, v[i]) for i in v}
 def getg(self, id) : return getDefault(self._v, str(id), CachedGuild(id, {}))
 def getall(self):
  out = {}
  for e in self._v: out.update({e: self._v[e].dictify()})
  return out
 def getids(self) : return [int(e) for e in self._v]
 def setg(self, id, value): self._v.update({str(id): value})
 def addg(self, value): self._v.update({str(value.id): value})
 def remg(self, id):
  try: self._v.pop(str(id))
  except KeyError:
   pass
  
 
class CachedGuild:
 def __init__(self, id, jsonDict=None):
  if jsonDict is None: jsonDict = {}
  self.id = id
  self.verif_role = jsonDict.get('verif_role')
  self.verif_msg = Message.from_dict(getDefault(jsonDict, 'verif_msg', {}))
  self.verif_log_msg = Message.from_dict(getDefault(jsonDict, 'verif_log_msg', {}))
  self.verif_log_channel = jsonDict.get('verif_log_channel')
  self.verif_timeout = getDefault(jsonDict, 'verif_timeout', TimeUnits.hour)
  self.verif_admin_timeout = getDefault(jsonDict, 'verif_admin_timeout', 2*TimeUnits.day)
  self.verif_pending = [UserCache.from_dict(e) for e in getDefault(jsonDict, 'verif_pending', [])]
  self.verif_admin_pending = [UserCache.from_dict(e) for e in getDefault(jsonDict, 'verif_admin_pending', [])]
 def verif_msg_from_dict(self, verif_msg): self.verif_msg = Message.from_dict(verif_msg)
 def verif_log_msg_from_dict(self, verif_log_msg): self.verif_log_msg = Message.from_dict(verif_log_msg)
 def dictify(self, shorten=True):
  dictified = {'verif_role': self.verif_role,'verif_msg': self.verif_msg.dictify(),'verif_log_msg': self.verif_log_msg.dictify(),'verif_log_channel': self.verif_log_channel,'verif_timeout': self.verif_timeout,'verif_admin_timeout': self.verif_admin_timeout,'verif_pending': [e.dictify() for e in self.verif_pending],'verif_admin_pending': [e.dictify() for e in self.verif_admin_pending]}
  if shorten: dictified = filter_none(dictified)
  return dictified
 
class UserCache:
 def __init__(self, id, created_at=None):
  self.id = id
  self.created_at = created_at if created_at is not None else time.time()
 @classmethod
 def from_dict(cls, jsonDict):
  id = jsonDict.get('id')
  created_at = jsonDict.get('created_at')
  return cls(id, created_at)
 def dictify(self) : return {'id': self.id,'created_at':  self.created_at}
 
class Message:
 def __init__(self, content='', embeds=None, files=None, delete_after=None, reference=None, poll=None, stickers=None, silent=False, mention_author=True, ephemeral=False, view=None):
  for x in embeds, files, stickers:
   if x is None: x = []
  self.content = content
  self.embeds = embeds
  self.files = files
  self.delete_after = delete_after
  self.reference = reference
  self.poll = poll
  self.stickers = stickers
  self.silent = silent
  self.mention_author = mention_author
  self.ephemeral = ephemeral
  self.view = view
  
 @property
 def adapted_files(self):
  if self.files is not None : return [e for e, u in self.files]
  return None
 @classmethod
 def from_dict(cls, jsonDict):
  content = getDefault(jsonDict, 'content', '')
  embedDict = getDefault(jsonDict, 'embeds', [])
  for e in embedDict:
   if (f := e.get("color")) is not None and f.__class__ != int: e.update({"color": int(f, 0)})
  embeds = [discord.Embed.from_dict(e) for e in embedDict]
  files = [(discord.File(io.BytesIO(requests.get(url := getDefault(e, 'url', None)).content),filename=getDefault(e, 'filename', None),description=getDefault(e, 'description', None),spoiler=getDefault(e, 'spoiler', False)),url) for e in getDefault(jsonDict, 'files', [])]
  poll = jsonDict.get('poll')
  if poll is not None: poll = discord.Poll(poll.get('question'), answers=[discord.PollAnswer(e.get('text'),emoji=(discord.PartialEmoji.from_str(emoji)if (emoji := e.get('emoji')) is not None else None)) for e in poll.get('answers')],duration=poll.get('duration'),allow_multiselect=getDefault(poll, 'allow_multiselect', False))
  stickers = getDefault(jsonDict, 'stickers', [])
  delete_after = jsonDict.get('delete_after')
  reference = jsonDict.get('reference')
  silent = getDefault(jsonDict, 'silent', False)
  mention_author = getDefault(jsonDict, 'mention_author', True)
  ephemeral = getDefault(jsonDict, 'ephemeral', False)
  return cls(content, embeds, files, delete_after, reference, poll, stickers, silent, mention_author, ephemeral)
 def set_view(self, view):
  self.view = view
  return self
 def dictify(self, shorten=True):
  embedList = [e.to_dict() for e in self.embeds]
  for e in embedList:
   if (f := e.get("color")) is not None: e.update({"color": hex(f)})
  dictified = {'content': self.content,'embeds': embedList,'files': [{"url": u,"filename": e.filename,"description": e.description,"spoiler": e.spoiler} for e, u in self.files],'poll':  {"duration": self.poll.duration,"allow_multiselect": self.poll.allow_multiselect,"question": self.poll.question.text,"answers": [{"emoji": str(e.media.emoji),"text": str(e.media.text),"voters": [u.id for u in e.voters()]} for e in self.poll.answers]} if self.poll is not None else None,'stickers': self.stickers,'delete_after': self.delete_after,'reference': self.reference,'silent': self.silent,'mention_author': self.mention_author,'ephemeral': self.ephemeral}
  if shorten: dictified = filter_none(dictified)
  return dictified
 async def send(self, ctx):
  if isAuth(ctx):
   return_message = await ctx.send(content=self.content,embeds=self.embeds,files=self.adapted_files,delete_after=self.delete_after,reference=(await ctx.channel.fetch_message(ctx.message.id if r <= 0 else r)if (r := self.reference) is not None else None),poll=self.poll,silent=self.silent,mention_author=self.mention_author,stickers=[await bot.fetch_sticker(e) for e in self.stickers])
   return return_message
  await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
 async def respond(self, ctx):
  return_message = await ctx.respond(content=self.content,embeds=self.embeds,files=self.adapted_files,delete_after=self.delete_after,ephemeral=self.ephemeral,view=self.view)
  return return_message
 
ext = Ext()
bot = theClient()
@tasks.loop(seconds=5)
async def usercheck_task():await bot.usercheck()
def isAuth(ctx):
 if isinstance(ctx, commands.Context) : return not isinstance(ctx.channel, discord.abc.GuildChannel) or ctx.author.guild_permissions.manage_webhooks
 return True
isVerAuth = lambda ctx:ctx.author.guild_permissions.manage_guild
isPinAuth = lambda ctx:ctx.author.guild_permissions.manage_messages
isReactAuth = lambda ctx:ctx.author.guild_permissions.add_reactions
isInteractionVerAuth = lambda interaction:interaction.user.guild_permissions.manage_guild
messagesGroup = bot.create_group("wh", "Sending webhook-style messages")
messagesResponseGroup = bot.create_group("r", "Sending response messages")
utilityGroup = bot.create_group("u", "Various QOL commands")
async def embed(ctx, message):
 try:
  await Message.from_dict(safeload(message)).send(ctx)
  await Message('Message sent!', ephemeral=True, delete_after=5.0).respond(ctx)
  return 
 except:
  pass
 await Message('Message failed to send!', ephemeral=True).respond(ctx)
async def rembed(ctx, message):
 try:
  message = Message.from_dict(safeload(message))
  message.poll = None
  await message.respond(ctx)
  return 
 except:
  pass
 await Message('Message failed to send!', ephemeral=True).respond(ctx)
@messagesGroup.command(name = "embed", description = "Send a message based on a json string")
async def embedstr(ctx, *, message: str):await embed(ctx, message)
@messagesGroup.command(name = "file-embed", description = "Send a message based on a json file")
async def embedf(ctx, *, json_file: discord.Attachment):await embed(ctx, await json_file.read())
@messagesGroup.command(name = "say", description = "Say something")
async def say(ctx, *, message: str):
 message = message.replace('\\\\n', '\\n').replace('\\n', '\n')
 await embed(ctx, f'{{"content":"{message}"}}')
@messagesGroup.command(name = "closepoll", description = "Close a poll")
async def closepoll(ctx, *, message_id: str):
 try:
  assert isAuth(ctx)
  await (await ctx.fetch_message(message_id)).end_poll()
  await Message('Poll closed!', ephemeral=True).respond(ctx)
  return 
 except:
  pass
 await Message('Poll closing failed!', ephemeral=True).respond(ctx)
@messagesGroup.command(name = "pin", description = "Pin a message")
async def pin(ctx, *, message_id: str, reason:str=None):
 try:
  assert isPinAuth(ctx)
  assert isAuth(ctx)
  await (await ctx.fetch_message(message_id)).pin(reason=reason)
  await Message('Message pinned!', ephemeral=True).respond(ctx)
  return 
 except:
  pass
 await Message('Message pinning failed!', ephemeral=True).respond(ctx)
@messagesGroup.command(name = "unpin", description = "Unpin a message")
async def pin(ctx, *, message_id: str, reason:str=None):
 try:
  assert isPinAuth(ctx)
  assert isAuth(ctx)
  await (await ctx.fetch_message(message_id)).unpin(reason=reason)
  await Message('Message unpinned!', ephemeral=True).respond(ctx)
  return 
 except:
  pass
 await Message('Message unpinning failed!', ephemeral=True).respond(ctx)
@messagesGroup.command(name = "react", description = "React to a message")
async def react(ctx, *, message_id: str, emoji: str):
 try:
  assert isAuth(ctx)
  await (await ctx.fetch_message(message_id)).add_reaction(discord.PartialEmoji.from_str(emoji))
  await Message('Reaction added!', ephemeral=True).respond(ctx)
  return 
 except:
  pass
 await Message('Reaction failed!', ephemeral=True).respond(ctx)
@messagesResponseGroup.command(name = "embed", description = "Respond with a message based on a json string")
async def rembedstr(ctx, *, message: str):await rembed(ctx, message)
@messagesResponseGroup.command(name = "file-embed", description = "Respond with a message based on a json file")
async def rembedf(ctx, *, json_file: discord.Attachment):await rembed(ctx, await json_file.read())
@messagesResponseGroup.command(name = "say", description = "Respond by saying something")
async def rsay(ctx, *, message: str):await Message(message.replace('\\\\n', '\\n').replace('\\n', '\n')).respond(ctx)
@messagesResponseGroup.command(name = "delete", description = "Deletes a message")
async def delete(ctx, *, message_id: str):
 try:
  reference_message = await ctx.fetch_message(message_id)
  if isAuth(ctx) or reference_message.interaction.user.id == ctx.author.id:
   await reference_message.delete()
   await Message('Message deleted successfully!', ephemeral=True).respond(ctx)
   return 
  
 except discord.HTTPException:
  pass
 await Message('Message delete failed!', ephemeral=True).respond(ctx)
@utilityGroup.command(name = "codeblock", description = "Converts message to a codeblock")
async def codeblock(ctx, message):
 await Message(f'```{message}```', ephemeral=True).respond(ctx)
@utilityGroup.command(name = "buzz", description="Sends the bot's latency.")
async def ping(ctx):
 await Message(f'Buzz! Latency is `{bot.latency}`', ephemeral=True).respond(ctx)
@utilityGroup.command(name = "newlinify", description = "Turn newlines into \\n")
async def newlinify(ctx, *, message_id: str):
 try:
  if reference_message := await ctx.fetch_message(message_id) and reference_message.content != '':
   await Message(reference_message.content.replace('\\n', '\\\\n').replace('\n','\\n'), ephemeral=True).respond(ctx)
   return 
  
 except discord.HTTPException:
  pass
 await Message('Newlinification failed!', ephemeral=True).respond(ctx)
def nativeMessageDictify(message, shorten=True):
 embeds = [e.to_dict() for e in message.embeds]
 for e in embeds:
  if (f := e.get("color")) is not None: e.update( {"color": hex(f)} )
 dictified = {"content": message.content,"embeds": embeds,"files": [{"url": e.url,"filename": e.filename,"description": e.description,"spoiler": e.is_spoiler()} for e in message.attachments],"reactions": [{"emoji": str(e.emoji),"users": [u.id for u in e.users()],"burst": e.me_burst} for e in message.reactions],"poll": {"duration": message.poll.duration,"allow_multiselect": message.poll.allow_multiselect,"question": message.poll.question.text,"answers": [{"emoji": str(e.media.emoji),"text": str(e.media.text),"voters": [u.id for u in e.voters()]} for e in message.poll.answers]} if message.poll is not None else None,"stickers": [e.id for e in message.stickers],"reference": message.reference.message_id if message.reference is not None else None,"created_at": datetime.datetime.timestamp(message.created_at),"edited_at": datetime.datetime.timestamp(message.edited_at) if message.edited_at is not None else None}
 if shorten: dictified = filter_none(dictified)
 return dictified
@utilityGroup.command(name = "jsonify", description = "Turn a message into json")
async def jsonify(ctx, *, message_id: str):
 try:
  if reference_message := await ctx.fetch_message(message_id):
   await Message.from_dict({ "embeds": [ { "description": f"```json\n{json.dumps(nativeMessageDictify(reference_message), indent=4)}\n```"} ], "ephemeral": True }).respond(ctx)
   return 
  
 except discord.HTTPException:
  pass
 await Message('Jsonification failed!', ephemeral=True).respond(ctx)
verificationGroup = bot.create_group("v", "Various verification-related commands")
verificationGroup.contexts = [discord.InteractionContextType.guild]
@verificationGroup.command(name = "verify", description="Verifies you if you are unverified")
async def verify(ctx):
 try:
  guild = ext.guilds.getg(ctx.guild.id)
  if any(e.id == ctx.author.id for e in guild.verif_pending) and not any(e.id == ctx.author.id for e in guild.verif_admin_pending):
   await Message(InfoMsg.verification_accepted, ephemeral=True).respond(ctx)
   guilds = ext.guilds
   guild.verif_pending = [e for e in guild.verif_pending if e.id != ctx.user.id]
   guild.verif_admin_pending.append(UserCache(ctx.user.id))
   guilds.addg(guild)
   await manualVerificationMessage(ctx.user, guild).send(ctx.guild.get_channel(guild.verif_log_channel))
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.verification_denied, ephemeral=True, delete_after=3.0).respond(ctx)
@verificationGroup.command(name = "unvrole", description="Sets the unverified role")
async def unverified_role(ctx, *, role: discord.Role):
 try:
  if isVerAuth(ctx):
   await Message(InfoMsg.set_unverified_role(role.id), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_role = role.id
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "timeout", description="Sets the verification timeout")
async def timeout(ctx, *, amt: float, time_interval: discord.Option(str, choices=['s', 'm', 'h', 'd', 'w'])):
 try:
  if isVerAuth(ctx):
   seconds = float(amt*TimeUnits.unit_map(time_interval))
   await Message(InfoMsg.set_v_timeout(seconds), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_timeout = seconds
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "mtimeout", description="Sets the manual verification timeout")
async def admin_timeout(ctx, *, amt: discord.SlashCommandOptionType.number, time_interval: discord.Option(str, choices=['s', 'm', 'h', 'd', 'w'])):
 try:
  if isVerAuth(ctx):
   seconds = float(amt*TimeUnits.unit_map(time_interval))
   await Message(InfoMsg.set_mv_timeout(seconds), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_admin_timeout = amt*TimeUnits.unit_map(time_interval)
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "msg", description="Sets the verification message")
async def set_verif_msg(ctx, *, message: str):
 try:
  if isVerAuth(ctx):
   await Message(InfoMsg.set_v_message(jsonPrettify(message)), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_msg_from_dict(safeload(message))
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "logmsg", description="Sets the verif-log message template (_ _user_ _ - mention, _ _username_ _ - username, _ _id_ _ - id)")
async def set_verif_log_msg(ctx, *, message: str):
 try:
  if isVerAuth(ctx):
   await Message(InfoMsg.set_vlog_message(jsonPrettify(message)), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_log_msg_from_dict(safeload(message))
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "logchannel", description="Sets the verif-log channel")
async def set_verif_log_channel(ctx, *, channel: discord.TextChannel):
 try:
  if isVerAuth(ctx):
   await Message(InfoMsg.set_vlog_channel(channel.id), delete_after=15.0).respond(ctx)
   guilds = ext.guilds
   guild = guilds.getg(ctx.guild.id)
   guild.verif_log_channel = channel.id
   guilds.addg(guild)
   ext.guilds = guilds
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "get", description="Sends the current verification config")
async def config_get(ctx):
 try:
  if isVerAuth(ctx):
   guild = ext.guilds.getg(ctx.guild.id)
   await Message(f'## CONFIG FOR CURRENT GUILD\n\\> Unverified role set to <@&{guild.verif_role}>\n\\> Verification timeout set to {datetime.timedelta(seconds=guild.verif_timeout)}\n\\> Manual verification timeout set to {datetime.timedelta(seconds=guild.verif_admin_timeout)}\n\\> Verification message set to:\n```json\n{json.dumps(guild.verif_msg.dictify(), indent=4)}```\n\\> Verification log message template set to:\n```json\n{json.dumps(guild.verif_log_msg.dictify(shorten=True), indent=4)}```\n\\> Verification log channel set to <#{guild.verif_log_channel}>.',ephemeral=True).respond(ctx)
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
class manualVerificationView(discord.ui.View):
 id_get = lambda i: int(re.search(r'((?<=<@)\d*(?=>))', i.message.embeds[~0].footer.text).group(0))
 @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji='\u2714\uFE0F')
 async def verify_callback(self, button, interaction):
  if isInteractionVerAuth(interaction):
   id = manualVerificationView.id_get(interaction)
   guilds = ext.guilds
   guild_cache = guilds.getg((guild := interaction.guild).id)
   guild_cache.verif_admin_pending = [e for e in guild_cache.verif_admin_pending if e.id != id]
   await guild.get_member(id).remove_roles(guild.get_role(guild_cache.verif_role), reason='Verification complete')
   guilds.addg(guild_cache)
   ext.guilds = guilds
   await Message(InfoMsg.verification_success(id)).respond(interaction)
  await Message(InfoMsg.permission_error, ephemeral=True).respond(interaction)
 @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji='\u274C')
 async def reject_callback(self, button, interaction):
  if isInteractionVerAuth(interaction):
   id = manualVerificationView.id_get(interaction)
   await (guild := interaction.guild).kick(guild.get_member(id), reason=InfoMsg.verification_declined_audit)
   await Message(InfoMsg.verification_declined_success(id)).respond(interaction)
  await Message(InfoMsg.permission_error, ephemeral=True).respond(interaction)
 
username_display = lambda user: f'{user.name}{f"#{user.discriminator}" if user.discriminator != "0" else ""}'
def manualVerificationMessage(user, guild_cache):
 msg = json.dumps(guild_cache.verif_log_msg.dictify()).replace('_ _user_ _', f'<@{user.id}>').replace('_ _username_ _', username_display(user)).replace('_ _id_ _', str(user.id))
 msg = safeload(msg)
 embeds = getDefault(msg, 'embeds', [])
 embeds.append({'footer': { 'text': f'>> <@{user.id}> | {username_display(user)}', 'icon_url': user.avatar.url } })
 msg.update({'embeds': embeds})
 return Message.from_dict(msg)
@verificationGroup.command(name = "sendverif", description="Sends the predefined verification message")
async def send_verification(ctx):
 if isVerAuth(ctx):
  await ext.guilds.getg(ctx.guild.id).verif_msg.respond(ctx)
  return 
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
async def force_verification(ctx, user: discord.Member):
 if isVerAuth(ctx):
  guilds = ext.guilds
  try: guild_cache = guilds.getg(ctx.guild.id)
  except AttributeError:
   await Message(InfoMsg.member_presence_error, ephemeral=True).respond(ctx)
   return 
  guild_cache.verif_admin_pending = [e for e in guild_cache.verif_admin_pending if e.id != user.id]
  guild_cache.verif_pending = [e for e in guild_cache.verif_pending if e.id != user.id]
  await user.remove_roles(ctx.guild.get_role(guild_cache.verif_role), reason=InfoMsg.force_verification_success_audit)
  guilds.addg(guild_cache)
  ext.guilds = guilds
  await Message(InfoMsg.force_verification_success(user.id)).respond(ctx)
  return 
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "veriflist", description="Sends a list of all unverified users")
async def get_veriflist(ctx):
 try:
  if isVerAuth(ctx):
   guild = ext.guilds.getg(ctx.guild.id)
   if len(guild.verif_pending) > 0:
    await Message('\n'.join([f'<@{x.id}>, {f"{datetime.timedelta(seconds=guild.verif_timeout)-(datetime.datetime.utcfromtimestamp(time.time())-datetime.datetime.utcfromtimestamp(x.created_at))}".split(".", 2)[0]} left' for x in guild.verif_pending])).respond(ctx)
    return 
   await Message('There are no unverified users!').respond(ctx)
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@verificationGroup.command(name = "mveriflist", description="Sends a list of all manually unverified users")
async def get_mveriflist(ctx):
 try:
  if isVerAuth(ctx):
   guild = ext.guilds.getg(ctx.guild.id)
   if len(guild.verif_admin_pending) > 0:
    await Message('\n'.join([f'<@{x.id}>, {f"{datetime.timedelta(seconds=guild.verif_admin_timeout)-(datetime.datetime.utcfromtimestamp(time.time())-datetime.datetime.utcfromtimestamp(x.created_at))}".split(".", 2)[0]} left' for x in guild.verif_admin_pending])).respond(ctx)
    return 
   await Message('There are no manually unverified users!').respond(ctx)
   return 
  
 except:
  pass
 await Message(InfoMsg.permission_error, ephemeral=True).respond(ctx)
@bot.listen()
async def on_guild_join(guild):
 guilds = ext.guilds
 guilds.addg(await CachedGuild(guild.id))
 ext.guilds = guilds
@bot.listen()
async def on_guild_remove(guild):
 guilds = ext.guilds
 guilds.remg(guild.id)
 ext.guilds = guilds
@bot.listen()
async def on_member_join(member):
 guilds = ext.guilds
 guild_cache = guilds.getg((guild := member.guild).id)
 if not any(e.id == member.id for e in guild_cache.verif_pending):
  guild_cache.verif_pending.append(UserCache(member.id))
  guilds.addg(guild_cache)
  ext.guilds = guilds
 await member.add_roles(guild.get_role(ext.guilds.getg(guild.id).verif_role), reason=InfoMsg.verification_role_on_join_audit)
@bot.listen()
async def on_member_update(before, user):
 guilds = ext.guilds
 guild_cache = guilds.getg((guild := user.guild).id)
 if not (guild_cache.verif_role in [role.id for role in user.roles]):
  guild_cache.verif_admin_pending = [e for e in guild_cache.verif_admin_pending if e.id != user.id]
  guild_cache.verif_pending = [e for e in guild_cache.verif_pending if e.id != user.id]
  guilds.addg(guild_cache)
  ext.guilds = guilds
 elif user.id not in [e.id for e in guild_cache.verif_admin_pending] + [e.id for e in guild_cache.verif_pending]:
  guild_cache.verif_admin_pending.append(UserCache(user.id))
  guilds.addg(guild_cache)
  ext.guilds = guilds
 
bot.run(token)
