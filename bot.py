import discord
from discord.ext import commands
import os
import random
import configparser
import asyncio

# 讀取配置文件
config = configparser.ConfigParser()
config.read("my_config.ini" , encoding="utf-8")

# 從配置文件中讀取設置
BOT_TOKEN = config["settings"]["bot_token"]
MUSIC_FOLDER = config["settings"]["music_folder"]
FFMPEG_EXECUTABLE = config["settings"]["ffmpeg_executable"]
FFMPEG_OPTIONS = config["settings"]["ffmpeg_options"]
PATH_VISIBLE = config["settings"].getboolean("path_visible")

# 機器人設定
intents = discord.Intents.default()
intents.message_content = True #v2
bot = commands.Bot(command_prefix="!", intents=intents)

#目前播放的歌曲資訊
play_song_info = {}

def find_all_music_files(folder):
    """遍歷資料夾及子資料夾，獲取所有音樂檔案"""
    supported_extensions = ('.mp3', '.wav', '.flac', 'm4a', 'aac')  # 可擴展支持的音樂格式
    music_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(supported_extensions):
                music_files.append(os.path.join(root, file))
    return music_files

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
async def join(ctx):
    """讓機器人加入語音頻道"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("你需要先加入一個語音頻道！")

@bot.command()
async def leave(ctx):
    """讓機器人離開語音頻道"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("我目前不在語音頻道中！")

@bot.command()
async def play(ctx, *song_name):
    """點歌"""
    if not ctx.voice_client:
        await ctx.send("請先讓我加入一個語音頻道，使用 !join 指令。")
        return
    
    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("音樂資料夾中沒有音樂檔案！")
        return
    
    selected_song = []
    guild_id = ctx.guild.id
    for i in music_files:
        name = i.split("\\")[-1] #只取最後歌名
        if " ".join(song_name) in name: 
            selected_song.append(i)

    if selected_song:
        # 隨機選擇一首音樂
        music_file = random.choice(selected_song)
        music_path = os.path.join(MUSIC_FOLDER, music_file)
    else:
        music_file = random.choice(music_files)
        music_path = os.path.join(MUSIC_FOLDER, music_file)

    music_name = music_file.split("\\")[-1]

    play_song_info[guild_id] = {"name" : music_name , "is_looping" : False}
    # 播放音樂
    vc = ctx.voice_client
    vc.stop()  # 停止當前播放的音樂
    vc.play(discord.FFmpegOpusAudio(
        executable=FFMPEG_EXECUTABLE,  # 確保這裡的路徑正確
        source=music_path,
        options=FFMPEG_OPTIONS
    ))

    if PATH_VISIBLE:
        await ctx.send(f"正在播放: {music_file}")
    else:
        await ctx.send(f"正在播放: {music_name}")

@bot.command()
async def stop(ctx):
    """停止播放音樂並斷開語音頻道"""
    if ctx.voice_client:  # 檢查機器人是否已連接到語音頻道
        if ctx.voice_client.is_playing():
            guild_id = ctx.guild.id
            ctx.voice_client.stop()  # 停止播放音樂
            play_song_info[guild_id]["is_looping"] = False
            await ctx.send("播放已停止！")
    else:
        await ctx.send("未連接到語音頻道 使用 !join 加入")
    
@bot.command()
async def loop(ctx, *song_name):
    """循環播放資料夾中的音樂"""
    if not ctx.voice_client:
        await ctx.send("請先讓我加入一個語音頻道，使用 !join 指令。")
        return

    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("音樂資料夾中沒有音樂檔案！")
        return
    
    selected_song = []
    guild_id = ctx.guild.id
    for i in music_files:
        name = i.split("\\")[-1] #只取最後歌名
        if " ".join(song_name) in name: 
            selected_song.append(i)

    guild_id = ctx.guild.id

    async def play_next_song(e=None):
        """播放下一首音樂"""
        if music_files and play_song_info[guild_id]["is_looping"]:
            music_file = random.choice(music_files)
            music_path = os.path.join(MUSIC_FOLDER, music_file)
            music_name = music_file.split("\\")[-1]
            play_song_info[guild_id]["name"] = music_name
            if PATH_VISIBLE:
                await ctx.send(f"正在播放: {music_file}")
            else:
                await ctx.send(f"正在播放: {music_name}")
            vc.play(discord.FFmpegOpusAudio(
                executable=FFMPEG_EXECUTABLE,
                source=music_path,
                options=FFMPEG_OPTIONS
            ),  after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next_song(), main_loop).result()
            )

    vc = ctx.voice_client
    if vc.is_playing():
        if play_song_info[guild_id]["is_looping"]:
            vc.stop()
            return
        else:
            vc.stop()
    main_loop = asyncio.get_event_loop()
    if selected_song:
        # 隨機選擇一首音樂
        music_file = random.choice(selected_song)
        music_path = os.path.join(MUSIC_FOLDER, music_file)
        music_name = music_file.split("\\")[-1]
        play_song_info[guild_id] = {"name" : music_name , "is_looping" : True}
        vc.play(discord.FFmpegOpusAudio(
            executable=FFMPEG_EXECUTABLE,  # 確保這裡的路徑正確
            source=music_path,
            options=FFMPEG_OPTIONS
        ),  after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next_song(), main_loop).result()
        )
        if PATH_VISIBLE:
            await ctx.send(f"正在播放: {music_file}")
        else:
            await ctx.send(f"正在播放: {music_name}")
        await ctx.send("之後開始循環播放音樂！")


    else:
        play_song_info[guild_id] = {"name" : None, "is_looping" : True}
        await ctx.send("沒有指定歌曲 開始循環播放音樂！")
        await play_next_song()  # 開始播放

@bot.command()
async def list(ctx, *song_name):
    """列出音樂檔案"""
    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("❌ 音樂資料夾中沒有音樂檔案！")
        return

    # 使用更好的搜尋邏輯
    search_term = " ".join(song_name).lower()
    selected_songs = [
        file for file in music_files 
        if search_term in os.path.splitext(os.path.basename(file))[0].lower()
    ]
    
    # 建立嵌入訊息
    embed = discord.Embed(
        title="🎵 搜尋結果" if search_term else "🎵 所有音樂",
        color=discord.Color.blue()
    )

    # 準備顯示的檔案列表
    display_files = selected_songs if search_term else music_files
    if not display_files and search_term:
        await ctx.send(f"❌ 找不到包含 '{search_term}' 的歌曲")
        return

    # 分頁顯示結果
    SONGS_PER_PAGE = 10
    pages = [display_files[i:i + SONGS_PER_PAGE] 
            for i in range(0, len(display_files), SONGS_PER_PAGE)]
    
    current_page = 0

    def get_page_embed(page_num):
        embed = discord.Embed(
            title="🎵 搜尋結果" if search_term else "🎵 所有音樂",
            color=discord.Color.blue()
        )
        song_list = ""
        for idx, file in enumerate(pages[page_num], 1 + page_num * SONGS_PER_PAGE):
            name = os.path.splitext(os.path.basename(file))[0]
            song_list += f"`{idx}.` {name}\n"
        
        embed.description = song_list
        embed.set_footer(text=f"第 {page_num + 1} 頁，共 {len(pages)} 頁 | 總共 {len(display_files)} 首歌")
        return embed

    message = await ctx.send(embed=get_page_embed(0))
    
    # 如果只有一頁，不需要加反應
    if len(pages) <= 1:
        return

    # 添加翻頁反應
    reactions = ['⬅️', '➡️']
    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

            if str(reaction.emoji) == '➡️' and current_page < len(pages) - 1:
                current_page += 1
                await message.edit(embed=get_page_embed(current_page))
            elif str(reaction.emoji) == '⬅️' and current_page > 0:
                current_page -= 1
                await message.edit(embed=get_page_embed(current_page))

            await message.remove_reaction(reaction, user)

        except asyncio.TimeoutError:
            await message.clear_reactions()
            break

@bot.command()
async def now(ctx):
    guild_id = ctx.guild.id
    await ctx.send(play_song_info[guild_id]["name"])

bot.run(BOT_TOKEN)