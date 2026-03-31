"""Simple downloader wrapper around yt-dlp for manual format selection.

This script prompts the user for a video URL, destination directory, and preferred
download type. It can download audio-only MP3 files, MP4/WebM videos, or a
combined best audio/video stream.
"""

import os
import yt_dlp

def prompt_choice(prompt, choices):
    """Prompt the user to select one of several numbered options.

    Args:
        prompt (str): The question text shown to the user.
        choices (list[str]): The list of available option labels.

    Returns:
        int: The zero-based index of the selected option.
    """
    print(prompt)
    for index, choice in enumerate(choices, start=1):
        print(f"  {index}. {choice}")

    while True:
        selected = input("Choose an option: ").strip()
        if selected.isdigit() and 1 <= int(selected) <= len(choices):
            return int(selected) - 1
        print(f"Please enter a number between 1 and {len(choices)}.")


def format_label(fmt):
    """Build a readable label for a single format entry.

    Args:
        fmt (dict): A yt-dlp format dictionary.

    Returns:
        str: Human-readable format description.
    """
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
    """Return formats filtered by the requested type and quality.

    Args:
        formats (list[dict]): Available formats from yt-dlp metadata.
        chosen_format (str): Output type ('mp3', 'mp4', 'webm', or 'all').
        download_quality (int | None): Maximum height in pixels, or None for no limit.

    Returns:
        list[dict]: Formats matching the requested criteria.
    """
    candidates = []
    for fmt in formats:
        if chosen_format == 'mp3':
            # Keep only audio-only formats for MP3 extraction.
            if fmt.get('vcodec') != 'none':
                continue
        elif chosen_format in ('mp4', 'webm'):
            # Match explicit container type for video downloads.
            if fmt.get('ext') != chosen_format:
                continue

        if download_quality and fmt.get('height') is not None:
            # Exclude formats that exceed the user-selected maximum resolution.
            if fmt['height'] > download_quality:
                continue
        candidates.append(fmt)
    return candidates


def choose_download_quality():
    """Ask the user for a maximum video quality setting.

    Returns:
        int | None: The maximum height in pixels, or None for best available.
    """
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
    """Run the downloader workflow from user prompts to yt-dlp execution."""
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

    # Probe available formats without downloading the media.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])

    # Present the available download modes to the user.
    type_choices = ['mp3', 'mp4', 'webm', 'Show all available formats', 'Combination of best Audio and Video Stream']
    type_index = prompt_choice('Choose the download format type:', type_choices)
    download_format = type_choices[type_index]

    if download_format != 'Combination of best Audio and Video Stream':
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

    # Build download options for the selected format or combination.
    ydl_opts = {
        'outtmpl': os.path.join(target, '%(title)s.%(ext)s'),
        'format': selected_format['format_id'] if download_format != 'Combination of best Audio and Video Stream' else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
    }

    if download_format == 'mp3':
        # Convert the downloaded audio stream to an MP3 file.
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    main()