import json
import os

from .config import PROFILES_FILE


DEFAULT_PROFILES = [
    {
        "name": "YouTube 1080p",
        "max_height": 1080,
        "min_fps": 0,
        "container": "mp4",
        "video_codec_pref": "h264",
        "audio_codec_pref": "any",
        "audio_only": False,
        "audio_bitrate": "192",
        "output_folder": "Videos",
        "subtitles": False,
        "thumbnail": False,
        "sponsorblock": False,
        "prefer_hdr": False,
    },
    {
        "name": "Music",
        "max_height": 0,
        "min_fps": 0,
        "container": "mp3",
        "video_codec_pref": "any",
        "audio_codec_pref": "any",
        "audio_only": True,
        "audio_bitrate": "320",
        "output_folder": "Music",
        "subtitles": False,
        "thumbnail": False,
        "sponsorblock": False,
        "prefer_hdr": False,
    },
    {
        "name": "Archive",
        "max_height": 2160,
        "min_fps": 0,
        "container": "mkv",
        "video_codec_pref": "any",
        "audio_codec_pref": "any",
        "audio_only": False,
        "audio_bitrate": "192",
        "output_folder": "Downloads",
        "subtitles": True,
        "thumbnail": True,
        "sponsorblock": False,
        "prefer_hdr": True,
    },
]


EMPTY_PROFILE = {
    "name": "Custom",
    "max_height": 1080,
    "min_fps": 0,
    "container": "mp4",
    "video_codec_pref": "any",
    "audio_codec_pref": "any",
    "audio_only": False,
    "audio_bitrate": "192",
    "output_folder": "",
    "subtitles": False,
    "thumbnail": False,
    "sponsorblock": False,
    "prefer_hdr": False,
}


def load_profiles():
    if not os.path.isfile(PROFILES_FILE):
        save_profiles(DEFAULT_PROFILES)
        return [dict(p) for p in DEFAULT_PROFILES]

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return [dict(p) for p in DEFAULT_PROFILES]


def save_profiles(profiles):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_profile_by_name(profiles, name):
    for p in profiles:
        if p.get("name") == name:
            return p
    return None


def resolve_output_dir(profile, current_output_dir):
    """Turn a profile's output_folder into an absolute path.
    - empty       -> use current_output_dir
    - absolute    -> use as-is
    - relative    -> current_output_dir / name
    """
    if not profile:
        return current_output_dir
    folder = (profile.get("output_folder") or "").strip()
    if not folder:
        return current_output_dir
    if os.path.isabs(folder):
        target = folder
    else:
        target = os.path.join(current_output_dir, folder)
    try:
        os.makedirs(target, exist_ok=True)
    except Exception:
        return current_output_dir
    return target