batchypegger
============

Apply ffmpeg in a simpler batchy way. 

Easily shrink a video, or a folder of videos.

Turn that 50 gig TV series into a 5 gig folder. Turn that silly-sized screen recording into something you can upload.

Cleans up the filenames too.

Install
=======

First install:
- ffmpeg (and put it in your system path)
- Python 3

Then install it with the `pip` command:

`pip install batchypegger`

Run it once to automatically create the config file `~/.batchypegger.yaml` and you're ready to go!

Examples
========   
- Shrink all videos in the current folder to 360p:

   `batchypegger 360p .`

- Shrink all the videos in the current folder without scaling them:
    
    `batchypegger .`

- What about just a file?

    `batchypegger 480p somevideo.mkv`

- Do a dry run to examine everything and make sure the filenames are right and the subtitles are picked up and stuff (good idea to do one first):

    `batchypegger . dry`

- Make a few different sizes:

   `batchypegger 360p 480p 720p 1080p .`

- Make a few different sizes but only the first 5 minutes (taster mode):

   `batchypegger taster 360p 480p 720p 1080p .`

- BTW, mode switches `taster` and `dry` can appear anywhere. These are all the same:

    `batchypegger 720p . dry `

    `batchypegger 720p . dry taster`
    
    `batchypegger taster dry 720p .`



- different schemes can be defined in the config file and then specified. This one will output 3 videos:

    `batchypegger x265 1080p 720p x264 360p somevideo.webm`
    
    ```
    Outputs: 
        somevideo__x265_720p.mkv
        somevideo__x265_1080p.mkv
        somevideo__x264_360p.mp4
    ```

Subtitles
=========

If there is an `.srt` or `.vtt` file with the same exact filename as the video, only difference being the extension, then it will include the subtitles in the output.

If you do a dry run, you can see if it picked up the subtitles or not.

DVD Subtitles
=============

If there is an `.idx` and `.sub` file with the same exact filename as the video, only difference being the extension, then it will pick them up. 

However, with DVD subtitles you need to use one of the `dvdsubs` profiles: `x264dvdsubs` or `x265dvdsubs`

Or use your own custom profile that uses `-c:s dvdsubs` in the codec args and maps what you need, examine the config yaml for insight.

If you do a dry run, you can see if it picked up the subtitles or not.

Cleaning Filenames
==================
It cleans the filenames. Someday this will be more configurable.

It will replace most characters with underscores and remove entire phrases that you've specified in the configuration section `just_erase`. 

For example if you had filenames like: `KittyShow 1x03 Freddy's birds (1080p BRrip x265 BooYeah).mkv`, just paste ` (1080p BRrip x265 BooYeah)` into `just_erase` in the config yaml, and do a dry run to make sure it got them. The output filenames would then look something like: `KittyShow_1x03_Freddy_s_birds__x264_360p.mp4`


Ignoring a file
===============
Rename the file to end with `__keep`, like `somevideo__keep.webm`, and it won't be processed.

I want advanced ffmpeg arguments
================================
Go ahead and edit the configuration file. Add as many schemes as you need. The ffmpeg command will be created like:

`ffmpeg ffargs_prefix scheme_prefix -i infile codec_args scaling scheme_suffix ffargs_suffix outfile`

and you can customise most of those in the config file. (`scaling` is calculated if you specify `480p` etc) 

Configuration: `~/.batchypegger.yaml`
====================================

The first time you run batchypegger, the configuration file will be created in your home folder: `~/.batchypegger.yaml` (On Windows that's like `C:\Users\DingleToes\.batchypegger.yaml`)

I tried to pick reasonable defaults. You can make new schemes for whatever you need. `tag` is what will be added to the filename, as in `foo__x264_720p.mp4`.

```yaml
# full path to ffmpeg executable, or auto to look in the system path.
ffmpeg: auto

# the args parser will enforce only recognised numbers for p-ness (480p, 720p, etc)
# although the scaling math will probably do any number you need, just add it in here
# just the numbers, like [320, 300, 2000]
allow_p: []

# the command will be constructed as:
#   ffmpeg ffargs_prefix scheme_prefix -i infile codec_args scaling scheme_suffix ffargs_suffix outfile
ffargs_prefix: 
ffargs_suffix: -max_muxing_queue_size 1024 -movflags faststart

default_scheme: x264
schemes:
  x264: 
    codec_args: -c:v libx264 -crf 28 -c:s mov_text
    format: mp4
    tag: x264
    prefix:
    suffix:

  x264mkv: 
    codec_args: -c:v libx264 -crf 28 -c:s srt
    format: mkv
    tag: x264
    prefix:
    suffix:

  x264dvdsub: 
    codec_args: -map 0:v -map 0:a -map 1:s -c:v libx264 -crf 28 -c:a copy -c:s dvdsub
    format: mkv
    tag: x264
    prefix:
    suffix:

  x265: 
    codec_args: -c:v libx265 -crf 30 -c:s srt
    format: mkv
    tag: x265
    prefix:
    suffix:

  x265dvdsub: 
    codec_args: -map 0:v -map 0:a -map 1:s -c:v libx265 -crf 30 -c:s dvdsub
    format: mkv
    tag: x265
    prefix:
    suffix:

just_erase: [
  " (480p DVD x265 BooYeah)",
  " (480p x265 BooYeah)",
  # this list can get big...
]
    

```
