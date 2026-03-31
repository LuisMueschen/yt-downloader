import yt_dlp

url = input("Video URL: ")
target = input("Target directory: ")

ydl_opts = {
    'outtmpl': target+'%(title)s.%(ext)s',
    'format': 'best'
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])