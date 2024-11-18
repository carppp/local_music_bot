import discord
from discord.ext import commands
import os
import random
import configparser

#TODO
#停止
#下一首
#點歌名(模糊搜尋)

# 讀取配置文件
config = configparser.ConfigParser()
config.read("config.ini" , encoding="utf-8")

# 從配置文件中讀取設置
BOT_TOKEN = config["settings"]["bot_token"]
MUSIC_FOLDER = config["settings"]["music_folder"]
FFMPEG_EXECUTABLE = config["settings"]["ffmpeg_executable"]
FFMPEG_OPTIONS = config["settings"]["ffmpeg_options"]

# 機器人設定
intents = discord.Intents.default()
intents.message_content = True #v2
bot = commands.Bot(command_prefix="!", intents=intents)

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
async def play(ctx):
    """播放資料夾中的音樂"""
    if not ctx.voice_client:
        await ctx.send("請先讓我加入一個語音頻道，使用 !join 指令。")
        return

    # 獲取音樂檔案列表
    music_files = find_all_music_files(MUSIC_FOLDER)
    if not music_files:
        await ctx.send("音樂資料夾中沒有音樂檔案！")
        return

    # 隨機選擇一首音樂
    music_file = random.choice(music_files)
    music_path = os.path.join(MUSIC_FOLDER, music_file)

    # 播放音樂
    vc = ctx.voice_client
    vc.stop()  # 停止當前播放的音樂
    vc.play(discord.FFmpegOpusAudio(
        executable=FFMPEG_EXECUTABLE,  # 確保這裡的路徑正確
        source=music_path,
        options=FFMPEG_OPTIONS
    ), after=lambda e: print(f"完成播放: {music_file}"))

    await ctx.send(f"正在播放: {music_file}")

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

    def play_next_song(e=None):
        """播放下一首音樂"""
        if music_files:
            music_file = random.choice(music_files)
            music_path = os.path.join(MUSIC_FOLDER, music_file)
            vc.play(discord.FFmpegOpusAudio(
                executable=FFMPEG_EXECUTABLE,
                source=music_path,
                options=FFMPEG_OPTIONS
            ), after=play_next_song)
            print(f"正在播放: {music_file}")

    vc = ctx.voice_client
    play_next_song()  # 開始播放
    await ctx.send("開始循環播放音樂！")

bot.run(BOT_TOKEN)