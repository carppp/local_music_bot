import discord
from discord.ext import commands
import os
import random
import configparser
import asyncio
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import base64
import io
from mutagen.mp4 import MP4, MP4Cover
from mutagen.easymp4 import EasyMP4

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

# 在檔案開頭定義支援的格式
SUPPORTED_EXTENSIONS = ('.mp3', '.wav', '.flac', '.m4a', '.aac')

def find_all_music_files(folder) -> list[str]:
    """遍歷資料夾及子資料夾，獲取所有音樂檔案"""
    music_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                music_files.append(os.path.join(root, file))
    return music_files

def get_song_name(file_path: str) -> str:
    """從檔案路徑獲取歌名（不含副檔名）"""
    return os.path.splitext(os.path.basename(file_path))[0]

def find_matching_songs(music_files: list[str], search_term: str) -> list[str]:
    """搜尋符合條件的歌曲，支援空白處理"""
    if not search_term:
        return []

    search_term = search_term.lower()
    search_words = search_term.split()
    
    matching_songs = []
    for file in music_files:
        song_name = get_song_name(file).lower()
        # 檢查所有搜尋詞是否都在歌名中
        if all(word in song_name for word in search_words):
            matching_songs.append(file)
            
    return matching_songs

def get_song_metadata(file_path: str) -> dict:
    """獲取音樂檔案的元數據，支援更多格式"""
    metadata = {"title": None, "artist": None, "album": None, "image": None}
    
    try:
        # 處理 M4A 檔案
        if file_path.lower().endswith('.m4a'):
            try:
                # 先嘗試使用 EasyMP4
                audio = EasyMP4(file_path)
                metadata["title"] = audio.get('title', [None])[0]
                metadata["artist"] = audio.get('artist', [None])[0]
                metadata["album"] = audio.get('album', [None])[0]

                # 讀取封面
                audio = MP4(file_path)
                if 'covr' in audio:
                    metadata["image"] = audio['covr'][0]
            except Exception as e:
                print(f"M4A 讀取失敗: {e}")

        # 處理 MP3 檔案
        elif file_path.lower().endswith('.mp3'):
            try:
                # 嘗試使用 ID3 讀取完整標籤
                audio = ID3(file_path)
                
                # 獲取標題
                if 'TIT2' in audio:
                    metadata["title"] = str(audio['TIT2'])
                
                # 獲取作者
                if 'TPE1' in audio:
                    metadata["artist"] = str(audio['TPE1'])
                elif 'TPE2' in audio:
                    metadata["artist"] = str(audio['TPE2'])
                
                # 獲取專輯
                if 'TALB' in audio:
                    metadata["album"] = str(audio['TALB'])
                
                # 獲取封面
                if 'APIC:' in audio:
                    metadata["image"] = audio['APIC:'].data
                elif 'APIC:Cover' in audio:
                    metadata["image"] = audio['APIC:Cover'].data
                else:
                    # 嘗試獲取其他 APIC 標籤
                    for key in audio.keys():
                        if key.startswith('APIC:'):
                            metadata["image"] = audio[key].data
                            break
            
            except Exception as e:
                print(f"ID3 讀取失敗，嘗試 EasyID3: {e}")
                try:
                    audio = EasyID3(file_path)
                    metadata["title"] = audio.get('title', [None])[0]
                    metadata["artist"] = audio.get('artist', [None])[0]
                    metadata["album"] = audio.get('album', [None])[0]
                except Exception as e:
                    print(f"EasyID3 讀取失敗: {e}")

        # 處理其他格式 (FLAC, WAV, AAC 等)
        else:
            audio = File(file_path)
            
            if hasattr(audio, 'tags'):
                tags = audio.tags
                
                # 嘗試不同的標籤格式
                for key in ['title', 'TITLE', 'TIT2']:
                    if key in tags:
                        metadata["title"] = str(tags[key][0])
                        break
                        
                for key in ['artist', 'ARTIST', 'TPE1']:
                    if key in tags:
                        metadata["artist"] = str(tags[key][0])
                        break
                        
                for key in ['album', 'ALBUM', 'TALB']:
                    if key in tags:
                        metadata["album"] = str(tags[key][0])
                        break

            # 嘗試獲取封面圖片
            if not metadata["image"]:
                if hasattr(audio, 'pictures'):
                    for pic in audio.pictures:
                        if pic.type == 3:  # 封面圖片
                            metadata["image"] = pic.data
                            break
                elif hasattr(audio, 'tags'):
                    # 檢查是否有其他格式的圖片標籤
                    for key in ['APIC:', 'APIC:Cover', 'covr', 'COVER_ART']:
                        if key in audio.tags:
                            metadata["image"] = audio.tags[key].data
                            break

    except Exception as e:
        print(f"讀取音樂檔案元數據時發生錯誤: {e}")

    # 清理元數據中的特殊字符和多餘空格
    for key in ['title', 'artist', 'album']:
        if metadata[key]:
            metadata[key] = metadata[key].strip()
            # 移除可能的引號
            if metadata[key].startswith('"') and metadata[key].endswith('"'):
                metadata[key] = metadata[key][1:-1]
            if metadata[key].startswith("'") and metadata[key].endswith("'"):
                metadata[key] = metadata[key][1:-1]

    return metadata

async def send_song_info(ctx, song_path: str, title_prefix: str = "🎵 現正播放"):
    """發送歌曲資訊的通用函數"""
    try:
        metadata = get_song_metadata(song_path)
        
        embed = discord.Embed(
            title=title_prefix,
            color=discord.Color.green()
        )

        # 添加基本資訊
        file_name = get_song_name(song_path)
        embed.add_field(
            name="檔案名稱", 
            value=file_name,
            inline=False
        )

        # 添加元數據資訊（如果有的話）
        if metadata["title"]:
            embed.add_field(name="標題", value=metadata["title"], inline=True)
        if metadata["artist"]:
            embed.add_field(name="作者", value=metadata["artist"], inline=True)
        if metadata["album"]:
            embed.add_field(name="專輯", value=metadata["album"], inline=True)

        # 如果有專輯封面，添加為縮圖
        if metadata["image"]:
            try:
                image = io.BytesIO(metadata["image"])
                file = discord.File(image, filename="album_cover.png")
                embed.set_thumbnail(url="attachment://album_cover.png")
                await ctx.send(file=file, embed=embed)
            except Exception as e:
                print(f"處理封面圖片時發生錯誤: {e}")
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
    except Exception as e:
        print(f"發送歌曲資訊時發生錯誤: {e}")
        await ctx.send(f"**{title_prefix}**: {get_song_name(song_path)}")

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
async def play(ctx, *, song_name: str = ""):
    """播放指定歌曲或隨機播放"""
    try:
        if not ctx.voice_client:
            await ctx.send("❌ 請先使用 !join 讓我加入語音頻道")
            return

        music_files = find_all_music_files(MUSIC_FOLDER)
        if not music_files:
            await ctx.send("❌ 音樂資料夾中沒有音樂檔案！")
            return

        selected_songs = find_matching_songs(music_files, song_name)
        
        if not selected_songs and song_name:
            await ctx.send(f"❌ 找不到包含 '{song_name}' 的歌曲")
            return

        # 選擇要播放的歌曲
        music_file = random.choice(selected_songs if selected_songs else music_files)
        
        # 播放音樂
        source = discord.FFmpegOpusAudio(
            executable=FFMPEG_EXECUTABLE,
            source=music_file,
            options=FFMPEG_OPTIONS
        )
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        
        ctx.voice_client.play(source)
        
        # 更新播放資訊
        guild_id = ctx.guild.id
        play_song_info[guild_id] = {
            "name": get_song_name(music_file),
            "is_looping": False
        }

        # 顯示歌曲資訊
        await send_song_info(ctx, music_file)

    except Exception as e:
        print(f"播放時發生錯誤: {e}")
        await ctx.send(f"❌ 播放時發生錯誤: {str(e)}")

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
async def loop(ctx, *, song_name: str = ""):
    """循環播放音樂"""
    try:
        if not ctx.voice_client:
            await ctx.send("❌ 請先使用 !join 讓我加入語音頻道")
            return

        guild_id = ctx.guild.id
        music_files = find_all_music_files(MUSIC_FOLDER)
        selected_songs = find_matching_songs(music_files, song_name)
        main_loop = asyncio.get_event_loop()

        async def play_next_song(e=None):
            """播放下一首音樂"""
            if not play_song_info[guild_id]["is_looping"]:
                return
                
            next_song = random.choice(selected_songs if selected_songs else music_files)
            source = discord.FFmpegOpusAudio(
                executable=FFMPEG_EXECUTABLE,
                source=next_song,
                options=FFMPEG_OPTIONS
            )
            
            if ctx.voice_client:
                ctx.voice_client.play(
                    source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        play_next_song(), main_loop
                    ).result()
                )
                
                # 更新播放資訊
                play_song_info[guild_id]["name"] = get_song_name(next_song)
                
                # 顯示歌曲資訊
                await send_song_info(ctx, next_song)

        # 處理循環播放邏輯
        if not song_name and guild_id in play_song_info and play_song_info[guild_id]["is_looping"]:
            play_song_info[guild_id]["is_looping"] = False
            ctx.voice_client.stop()
            await ctx.send("⏹️ 已停止循環播放")
            return

        # 開始新的循環播放
        if selected_songs or not song_name:
            play_song_info[guild_id] = {"name": None, "is_looping": True}
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            await play_next_song()
            await ctx.send("🔄 開始循環播放！")
        else:
            await ctx.send(f"❌ 找不到包含 '{song_name}' 的歌曲")

    except Exception as e:
        print(f"循環播放時發生錯誤: {e}")
        await ctx.send(f"❌ 循環播放時發生錯誤: {str(e)}")

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
    """顯示當前播放的歌曲資訊"""
    guild_id = ctx.guild.id
    if guild_id not in play_song_info or not play_song_info[guild_id]["name"]:
        await ctx.send("❌ 目前沒有播放任何音樂")
        return

    # 獲取完整的檔案路徑
    current_song = None
    music_files = find_all_music_files(MUSIC_FOLDER)
    for file in music_files:
        if get_song_name(file) == play_song_info[guild_id]["name"]:
            current_song = file
            break

    if not current_song:
        await ctx.send("❌ 找不到當前播放的音樂檔案")
        return

    # 顯示歌曲資訊
    await send_song_info(ctx, current_song)

bot.run(BOT_TOKEN)