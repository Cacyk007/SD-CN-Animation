import launch

import os

req_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")


def open(req_file):
    pass

c
with open(req_file) as file:

    for lib in file:

        lib = lib.strip()

        if not launch.is_installed(lib):

            launch.run_pip(f"install {lib}", f"SD-CN-Animation requirement: {lib}")


import os
from moviepy.editor import VideoFileClip

path = "C:/Users/Kris/input_movies"
duration = 55  # length of each short video in seconds
output_dir = "C:/Users/Kris/output_movies"
os.makedirs(output_dir, exist_ok=True)


def split_video(input_video, duration):
    clip = VideoFileClip(input_video)
    total_duration = clip.duration

    for i in range(0, int(total_duration), duration):
        start_time = i
        end_time = min(i + duration, total_duration)
        subclip = clip.subclip(start_time, end_time)
        output_filename = os.path.join(output_dir,
                                       f"{os.path.splitext(os.path.basename(input_video))[0]}_{i // duration + 1}.mp4")
        subclip.write_videofile(output_filename)


def main():
    for filename in os.listdir(path):
        if filename.endswith(".mkv"):
            input_file = os.path.join(path, filename)
            split_video(input_file, duration)
            print(f"######### completed {filename}")


if __name__ == '__main__':
    main()

