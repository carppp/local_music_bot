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

    6.點左邊OAuth2 在下面URL Generator那邊點bot 下面會出現要給的權限 目前功能的話只需要connect跟speak就好

    7.把最下面的Generated URL 複製下來就可以拉進伺服器了

    8.找到你想放音樂的資料夾 如果windows的話直接點上面路徑複製下來貼在music_folder那邊

    9.下面ffmpeg相關的如果有自己的版本或想改的參數可以自己修改

    10.最下面path_visible決定播歌的時候會不會把路徑一起發出來 預設為false

    11.點bot.exe 看到最後出現login [你的bot名字]就完成了

Command

    !join 讓機器人加進你現在的語音頻道中(沒有進頻道會報錯)

    !play [歌名] 如果沒打歌名就會從全部的歌裡隨便挑一首播
    有打的話就會從歌名找含那些字的隨便挑一首播

    !loop 隨便挑一首歌播然後開始循環播放(上面的指令只會播一首)

    !stop 停止播放 如果在循環中也會把循環停掉

    !list 把你資料夾中全部的歌的歌名打在聊天室中

    !now 跟你說現在在播哪首歌

    !leave 讓機器人離開頻道

