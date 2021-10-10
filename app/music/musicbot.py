from discord.ext import commands

from app.music.youtubesource import YoutubeDLSource
from app.music.musicembed import MusicEmbed
from app.music.musicplayer import MusicPlayer

class MusicBot(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.music_players = {}

    def get_music_player(self, ctx: commands.Context):
        music_player = self.music_players.get(ctx.guild.id)
        if not music_player:
            music_player = MusicPlayer(self.client, ctx)
            self.music_players[ctx.guild.id] = music_player
        
        return music_player

    def cog_unload(self):
        for music_player in self.music_players.values():
            self.client.loop.create_task(music_player.stop())

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.music_player = self.get_music_player(ctx)

    @commands.command(
        name="join", 
        description="Lets the bot join the current voice channel", 
        aliases=["j"], 
        invoke_without_subcommand=True
    )
    async def _join(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        if ctx.music_player.voice:
            await ctx.music_player.voice.move_to(channel)
            return

        ctx.music_player.voice = await channel.connect()
        await ctx.guild.get_member(self.client.user.id).edit(mute=False, deafen=True) # deafen the bot on enter
    
    @commands.command(
        name="disconnect",
        aliases=["d"],
        description="Music bot leaves the current channel."
    )
    async def _disconnect(self, ctx: commands.Context):
        if not ctx.music_player.voice:
            embed = MusicEmbed("WARNING", title="Can't Disconnect", description="I'm not even connected to any voice channel.")
            return await ctx.send(embed=embed)

        await ctx.music_player.stop()

        if ctx.music_player.is_inactive:
            embed = MusicEmbed(title="🔌 Disconnnected due to Inactivity.", description="Nangluod na ko walay kanta.")
        else:
            embed = MusicEmbed("NOTICE", title="Disconnected", description="It was a pleasure to play music for you.")
        await self.__ctx.send(embed=embed)
        await ctx.message.add_reaction("✅")

        del self.music_players[ctx.guild.id]

    @commands.command(
        name="play",
        aliases=["p"],
        description="Plays a track." 
    )
    async def _play(self, ctx: commands.Context, *, query: str):
        if not ctx.music_player.voice:
            await ctx.invoke(self._join)

        async with ctx.typing(): # shows typing in discord
            try:
                music = YoutubeDLSource().get_music(query, ctx)
            except Exception as e:
                await ctx.send(embed=MusicEmbed(title="Youtube Download Error", description=str(e)))
            else:
                await ctx.music_player.playlist.add(music)
                
                if ctx.music_player.is_playing:
                    embed = music.create_embed(header=f"📜 [{ctx.music_player.playlist.size()}] Music Queued")
                    await ctx.send(embed=embed)

    @commands.command(name="queue", aliases=["q"], description="Returns the list of songs in queue.")
    async def _queue(self, ctx: commands.Context, page: int = 1):
        size = ctx.music_player.playlist.size()

        if size != 0 and (page < 1 or page * 8 > size):
            embed = MusicEmbed("WARNING", title="Page Out of Range", description=f"It's not that big.")
            return await ctx.send(embed=embed) 

        await ctx.send(embed=ctx.music_player.playlist.create_embed(8, page))

    @commands.command(name="current", aliases=["curr"], description="Displays the currently active track.")
    async def _current(self, ctx: commands.Context):
        if ctx.music_player.current is None:
            embed = MusicEmbed("NOTICE", title="No Track Currently Playing", description="Maybe you can add some songs?")
        else:
            embed = ctx.music_player.current.create_embed(header="▶️ Currently Playing", show_tags=True)

        await ctx.send(embed=embed)

    @commands.command(name="skip", aliases=["s"], description="Skips the currently playing track.")
    async def _skip(self, ctx: commands.Context):
        if not ctx.music_player.is_playing:
            embed = MusicEmbed("NOTICE", title="No Track Currently Playing", description="Maybe you can add some songs?")
        else:
            ctx.music_player.skip()
            embed = ctx.music_player.current.create_embed(header="⏭ Skipped", simplified=True)
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(embed=MusicEmbed("WARNING", title="Command Error", description=str(error)))

    @commands.command(name="remove", aliases=["rm"], description="Removes a music with the given index from the queue.")
    async def _remove(self, ctx: commands.Context, idx: int = -1):
        max = ctx.music_player.playlist.size()
        if max == 0:
            embed = ctx.music_player.playlist.create_embed()
            return await ctx.send(embed=embed) 
        elif idx < 1 or idx > max:
            embed = MusicEmbed(title="Music Number out of Range", description=f"It's not that big.")
            return await ctx.send(embed=embed) 

        removed = ctx.music_player.playlist.remove(idx - 1)
        embed = removed.create_embed(header="❌ Removed From Queue", simplified=True)
        await ctx.send(embed=embed)

    @commands.command(name="shuffle", desciption="Shuffles the queue.")
    async def _shuffle(self, ctx: commands.Context):
        if ctx.music_player.playlist.size() == 0:
            return await ctx.send(embed=ctx.music_player.playlist.create_embed())
        
        ctx.music_player.playlist.shuffle()
        await ctx.send(embed=MusicEmbed(title="🔀 Queue Shuffled", description="Now, which is which?!"))
        await ctx.message.add_reaction("🔀")
        
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("Connect to a voice channel first.")

        # if ctx is in a voice_client but it is not the same voice_client as bot
        if hasattr(ctx.voice_client, "voice"):
            if ctx.voice_client.voice != ctx.author.voice.channel:
                raise commands.CommandError("I am already in a voice channel.")

    # Fix tomorrow
    # @_disconnect.before_invoke
    # @_skip.before_invoke
    # @_current.before_invoke
    # @_queue.before_invoke
    # @_remove.before_invoke
    # async def ensure_music_player(self, ctx: commands.Context):
    #     if not hasattr(ctx, "music_player") or not ctx.music_player.voice:
    #         raise commands.CommandError("I am not in a voice channel.")

def setup(client):
    client.add_cog(MusicBot(client))