Introduction

    這是一個可以自己創機器人撥本地音樂的小程式

Download

    放在realese了

Setup

    到discord的開發者網站註冊機器人
    https://discord.com/developers/applications

    流程:
    1.點左邊bot 

    2.放上你的bot想要的頭貼跟橫幅(option)

    3.改你的bot名字

    4.點名字那格下面的Reset Token

    5.過完認證後會獲得一串英數字 複製下來貼在config.ini中的bot_token欄位中

    6.點左邊OAuth2 在下面URL Generator那邊點bot 下面會出現要給的權限 要不要勾都可以 反正可以在加進去之後用身分組權限控制
    如果要先給好權限的話要選Send Messages, Add Reactions, Connect, Speak這四個

    7.把最下面的Generated URL 複製下來就可以拉進伺服器了

    8.找到你想放音樂的資料夾 如果windows的話直接點上面路徑複製下來貼在music_folder那邊

    9.下面ffmpeg相關的如果有自己的版本或想改的參數可以自己修改

    10.最下面path_visible決定播歌的時候會不會把路徑一起發出來 預設為false

    11.點bot.exe 看到最後出現login [你的bot名字]就完成了

Command

    !join 讓機器人加進你現在的語音頻道中(沒有進頻道會報錯)

    !play [關鍵字] 歌名找含那些字的隨便挑一首播
    如果沒打關鍵字就會從資料夾全部的歌裡隨便挑一首播

    !loop [關鍵字]開始循環播放(上面的指令只會播一首)(同樣支援點歌)

    !stop 停止播放 如果在循環中也會把循環停掉

    !list [關鍵字] 將包含關鍵字的歌名全部打在聊天室
    沒有的話就把資料夾中全部的歌的歌名打在聊天室中

    !now 跟你說現在在播哪首歌

    !leave 讓機器人離開頻道

Pyinstaller

    記錄用 如果想要自己打包的話也可以參考
    pyinstaller --hiddenimport _cffi_backend -F bot.py
