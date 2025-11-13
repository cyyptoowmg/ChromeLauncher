import os
import re

def extract_number(text):
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else 99999

def scan_profiles(shortcut_folder):
    profiles = []

    if not os.path.isdir(shortcut_folder):
        return profiles

    for file in os.listdir(shortcut_folder):
        if file.lower().endswith(".lnk"):
            full_path = os.path.join(shortcut_folder, file)
            profiles.append({
                "name": file.replace(".lnk", ""),
                "path": full_path
            })

    # 숫자 기반 자연 정렬
    profiles.sort(key=lambda x: extract_number(x["name"]))

    return profiles
