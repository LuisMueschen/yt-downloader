import os
import yt_dlp


def prompt_choice(prompt, choices):
    print(prompt)
    for index, choice in enumerate(choices, start=1):
        print(f"  {index}. {choice}")

    while True:
        selected = input("Choose an option: ").strip()
        if selected.isdigit() and 1 <= int(selected) <= len(choices):
            return int(selected) - 1
        print(f"Please enter a number between 1 and {len(choices)}.")


def format_label(fmt):
    resolution = fmt.get('resolution') or (
        f"{fmt.get('width')}x{fmt.get('height')}" if fmt.get('height') else "audio"
    )
    ext = fmt.get('ext', 'unknown')
    vcodec = fmt.get('vcodec', 'unknown')
    acodec = fmt.get('acodec', 'unknown')
    size = fmt.get('filesize')
    size_label = f"{size // 1024 // 1024}MB" if isinstance(size, int) else "unknown size"
    return f"{fmt['format_id']} | {ext} | {resolution} | v:{vcodec} a:{acodec} | {size_label}"


def filter_formats(formats, chosen_format, download_quality=None):
    candidates = []
    for fmt in formats:
        if chosen_format == 'mp3':
            if fmt.get('vcodec') != 'none':
                continue
        elif chosen_format in ('mp4', 'webm'):
            if fmt.get('ext') != chosen_format:
                continue
        if download_quality and fmt.get('height') is not None:
            if fmt['height'] > download_quality:
                continue
        candidates.append(fmt)
    return candidates


def choose_download_quality():
    choices = [
        'Best available',
        'HD (720p or lower)',
        'Full HD (1080p or lower)',
        '2K (1440p or lower)',
        '4K (2160p or lower)'
    ]
    selected = prompt_choice('Select video quality:', choices)
    return [None, 720, 1080, 1440, 2160][selected]


def main():
    url = input('Video URL: ').strip()
    target = input('Target directory: ').strip()
    if not target:
        target = os.getcwd()
    os.makedirs(target, exist_ok=True)
    if not target.endswith(os.sep):
        target = target + os.sep

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])

    type_choices = ['mp3', 'mp4', 'webm', 'Show all available formats']
    type_index = prompt_choice('Choose the download format type:', type_choices)
    download_format = type_choices[type_index]

    download_quality = None
    if download_format in ('mp4', 'webm'):
        download_quality = choose_download_quality()

    filtered_formats = filter_formats(
        formats,
        download_format if download_format != 'Show all available formats' else 'all',
        download_quality,
    )
    if not filtered_formats:
        print('No available formats match your selection.')
        return

    selected_format_index = prompt_choice(
        'Choose the exact format to download:',
        [format_label(fmt) for fmt in filtered_formats],
    )
    selected_format = filtered_formats[selected_format_index]

    ydl_opts = {
        'outtmpl': os.path.join(target, '%(title)s.%(ext)s'),
        'format': selected_format['format_id'],
    }

    if download_format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    main()