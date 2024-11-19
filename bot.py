import discord
from discord.ext import commands
import os
import random
import configparser
import asyncio

# 讀取配置文件
config = configparser.ConfigParser()
config.read("config.ini" , encoding="utf-8")

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
async def loop(ctx):
    """循環播放資料夾中的音樂"""
    if not ctx.voice_client:
        await ctx.send("請先讓我加入一個語音頻道，使用 !join 指令。")
        return

    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("音樂資料夾中沒有音樂檔案！")
        return

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
        vc.stop()
        return
    main_loop = asyncio.get_event_loop()
    play_song_info[guild_id] = {"name" : None, "is_looping" : True}
    await ctx.send("開始循環播放音樂！")
    await play_next_song()  # 開始播放

@bot.command()
async def list(ctx, *song_name):
    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("音樂資料夾中沒有音樂檔案！")
        return
    
    selected_song = []
    for i in music_files:
        name = i.split("\\")[-1] #只取最後歌名
        if " ".join(song_name) in name: 
            selected_song.append(i)
    
    # 決定要顯示的檔案列表
    display_files = selected_song if selected_song else music_files
    
    await ctx.send("搜尋結果:" if selected_song else "目前資料夾檔案:")

    msg = ""
    for i in display_files:
        name = i.split("\\")[-1]
        if len(msg) + len((name + "\n")) < 2000: #避免discord訊息過長 分段發送
            msg += (name + "\n")
        else:
            await ctx.send(msg)
            msg = ""

    if msg:  # 確保最後一段訊息也有發送
        await ctx.send(msg)

@bot.command()
async def now(ctx):
    guild_id = ctx.guild.id
    await ctx.send(play_song_info[guild_id]["name"])

bot.run(BOT_TOKEN)