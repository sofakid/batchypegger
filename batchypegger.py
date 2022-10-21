import os
import glob
import subprocess
import sys
import re
import shutil
import yaml

ALLOWED_P = [320, 360, 480, 720, 1080]
DRY_RUN = False
TASTER = False
JUST_ERASE = []
FORMAT = 'mp4'
FFARGS_PREFIX = ''
FFARGS_SUFFIX = ''
DEFAULT_SCHEME = ''
SCHEMES = dict()

ACTIONS = []
TARGETS = []

OUTFILES = []
FFMPEG = None

config_file = os.path.expanduser('~/.batchypegger.yaml')

def create_rc_file():
  with open(config_file, 'w') as f:
    print('''
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
]
    ''', file=f)

if os.path.exists(config_file):
  with open(config_file, 'r') as fd:
    figgy = yaml.safe_load(fd)
    for x in figgy['allow_p']:
      ALLOWED_P.append(x)
    for x in figgy['just_erase']:
      JUST_ERASE.append(x)

    x = figgy['ffargs_prefix']
    FFARGS_PREFIX = [] if x == None else x.split()

    x = figgy['ffargs_suffix']
    FFARGS_SUFFIX = [] if x == None else x.split()

    DEFAULT_SCHEME = figgy['default_scheme']
    SCHEMES = figgy['schemes']
    FFMPEG = figgy['ffmpeg']
else:
  create_rc_file()
  print("Created " + config_file + ". Go edit it and make any customisations there. Then come back and run your command again. ")
  exit()

ALLOWED_P_STR = []
ALLOWED_PS = []
for p in ALLOWED_P:
  ALLOWED_P_STR.append(str(p))
  ALLOWED_PS.append(str(p) + 'p')

ALLOWED_SCHEMES_MSG = '|'.join(SCHEMES.keys())
ALLOWED_PS_MSG = 'p|'.join(ALLOWED_P_STR) + 'p'

if FFMPEG == 'auto':
  FFMPEG = shutil.which('ffmpeg')
  if (FFMPEG == None):
    print('ffmpeg not found in system path. Go get it and put it in the path, or add the path to it under "ffmpeg" to your config file ~/.batchypegger.yaml please.')
    exit()

if not os.path.isfile(FFMPEG):
  print("Couldn't find " + FFMPEG)
  print('Please double check under "ffmpeg" in your config file ~/.batchypegger.yaml.')
  exit()

# =======================================================================================

def clean_filename(sin):
  global JUST_ERASE
  s = sin

  for to_erase in JUST_ERASE:
    s = s.replace(to_erase, "")

  s = s.replace("'", "").replace(",", "__").replace("&", "and").replace(" - ", "__")
  return re.sub('(\W+)','_', s)

def usage():
  print("usage:")
  print("  batchypegger taster? dry? ([{schemes}]* [{p}]*)* target_path ".format(schemes=ALLOWED_SCHEMES_MSG, p=ALLOWED_PS_MSG))

  exit()


def parse_args():
  global SCALE_RES, SCALE_SUFFIX, ACTIONS, TARGETS
  
  unfinished = False
  arg_consumed = False
  current_scheme = DEFAULT_SCHEME
  
  def q_action(pness):
    nonlocal unfinished
    o = dict()
    o['scheme'] = current_scheme
    o['pness'] = pness
    ACTIONS.append(o)
    unfinished = False

  def new_scheme(arg):
    nonlocal current_scheme, arg_consumed, unfinished
    if unfinished:
      q_action('noscale')

    current_scheme = arg
    arg_consumed = True
    unfinished = True

  def new_pness(arg):
    nonlocal arg_consumed, unfinished
    q_action(arg)
    arg_consumed = True
  
  def enable_taster():
    global TASTER
    nonlocal arg_consumed
    TASTER = True
    arg_consumed = True

  def enable_dry_run():
    global DRY_RUN
    nonlocal arg_consumed
    DRY_RUN = True
    arg_consumed = True

  if (len(sys.argv) <= 1):
    usage()

  for arg in sys.argv:
    print("checking arg: " + arg)
    if arg == 'batchypegger.py':
      continue

    if arg.endswith('batchypegger'):
      continue

    if arg.endswith('batchypegger.exe'):
      continue

    arg_consumed = False
    for scheme in SCHEMES:
      if arg == scheme:
        new_scheme(arg)

    if arg_consumed:
      continue  
    
    for p in ALLOWED_PS:
      if arg == p:
        new_pness(arg)

    if arg_consumed:
      continue  
    
    if arg == 'taster':
      enable_taster()
      continue
    
    if arg == 'dry':
      enable_dry_run()
      continue  

    if os.path.isdir(arg) or os.path.isfile(arg):
      TARGETS.append(arg)
      continue

    usage()

    
  if unfinished:
    q_action('noscale')

  if len(ACTIONS) == 0:
    q_action('noscale')

  if len(TARGETS) == 0:
    print("No target specified, appending cwd:" + os.getcwd())
    TARGETS.append(os.getcwd())

  print('actions')
  print(str(ACTIONS))

  print('TARGETS')
  print(str(TARGETS))
  
parse_args()

def dump_config():
  print("\n\n===============================================================")
  print("        ffmpeg: " + FFMPEG)
  print("     allowed p: " + ALLOWED_PS_MSG)
  print("       dry run: " + str(DRY_RUN))
  print("        taster: " + str(TASTER))
  print(" ffargs_prefix: " + str(FFARGS_PREFIX))
  print(" ffargs_suffix: " + str(FFARGS_SUFFIX))
  print("default_scheme: " + str(DEFAULT_SCHEME))
  # print("    just erase: ", end='')
  # for x in JUST_ERASE:
  #   print('"' + x + '"\n                ', end='')
  print("Schemes:" + str(SCHEMES))
  print("===================================================")

dump_config()

def header(s):
  print("\n\n==========================================================================================================================================================")
  print("==========================================================================================================================================================\n")
  print('   ' + s)
  print('   ' + s)
  print('   ' + s + '\n')
  print("==========================================================================================================================================================")
  print("==========================================================================================================================================================\n\n")
    
def make_tag(tag, i, n):
  return tag + ':(' + str(i) + '/' + str(n) + ')'

def make_folder_tag():
  global N_FOLDERS, I_FOLDER
  I_FOLDER += 1
  return make_tag('folder', I_FOLDER, N_FOLDERS)

# put the suffixes in here, so when we run it again to resume a 
# failed/aborted run we don't make stuff like ...__x264_720p__x264_720p.mp4
def glob_vids(but_nots):
  but_nots += ['__keep']

  # False if we should exclude this file
  def certainly_not(x, ext):
    for but_not in but_nots:
      if x.endswith(but_not + ext):
        return False
    return True

  def globby(extension):
    return list(filter(lambda x: certainly_not(x, extension), glob.glob('*' + extension)))

  # put the dot
  vids = globby('.webm')
  vids += globby('.avi')
  vids += globby('.mp4')
  vids += globby('.mkv')

  return vids

def get_scheme_tag(action):
  return get_scheme(action)['tag']

def make_suffix(action):
  x = action['pness']
  y = '' if x == 'noscale' else ('_' + x)
  t = '_Taster' if TASTER else ''
  return '__' + get_scheme_tag(action) + y + t

def get_scheme(action):
  return SCHEMES[action['scheme']]

def get_format(action):
  return get_scheme(action)['format']

def splitty(s):
  if s == None:
    return []
  return s.split()

def get_scheme_prefix(action):
  return splitty(get_scheme(action)['prefix'])

def get_scheme_suffix(action):
  return splitty(get_scheme(action)['suffix'])

def get_codec_args(action):
  return splitty(get_scheme(action)['codec_args'])

def get_subs(action):
  s = action['subs']
  return [ ] if s == None else [ '-i', s ]

def get_dvdsubs(action):
  s = action['dvdsubs']
  return [ ] if s == None else [ '-i', s + '.idx', '-i', s + '.sub' ]

  
def get_scaling(action):
  pness = action['pness']

  if pness == 'noscale':
    return []

  match = re.fullmatch(r'(\d+)p', pness)

  if match == None:
    print(ALLOWED_PS_MSG + " please, got: " + pness)
    usage()

  return ['-vf', 'scale=-2:' + str(int(match[1]))]

def get_taster(action):
  t = ['-ss', '0:0:0', '-to', '0:5:0']
  return t if TASTER else []

def make_suffixes():
  return list(map(make_suffix, ACTIONS))

def dumpy(o):
  print('src:' + o['infile'])
  print('\\->:' + o['outfile'] + '\n')

def look_for_subs(basename):
  for ext in ['.srt', '.vtt']:
    if os.path.isfile(basename + ext):
      return basename + ext
  return None

def look_for_dvdsubs(basename):
  i = 0
  for ext in ['.idx', '.sub']:
    if os.path.isfile(basename + ext):
      i += 1
  return basename if i == 2 else None

def do_convert_all_vids():
  basename_suffixes = make_suffixes()
  print("basename_suffixes: " + str(basename_suffixes))
  src_vids = glob_vids(basename_suffixes)
  print("src_vids: " + str(src_vids))
  convert_vids(src_vids)
  
def convert_vids(src_vids):
  global OUTFILES
  folder_tag = make_folder_tag()
  q = []
  for src_vid in src_vids:
    basename, extension = os.path.splitext(src_vid)
    subs = look_for_subs(basename)
    dvdsubs = look_for_dvdsubs(basename)
    clean_base = clean_filename(basename)
    for action in ACTIONS:
      o = dict() # yes, make a new one
      o['infile'] = src_vid
      o['outfile'] = clean_base + make_suffix(action) + '.' + get_format(action)
      o['scheme'] = action['scheme']
      o['pness'] = action['pness']
      o['subs'] = subs
      o['dvdsubs'] = dvdsubs
      #print('Appending:')
      #dumpy(o)
      q.append(o)

  print('Processing: ')
  for o in q:
    print("    : " + str(o))

  n_files = len(q)
  i_file = 0
  for o in q:

    i_file += 1
    file_tag = make_tag('file', i_file, n_files)

    infile = o['infile']
    outfile = o['outfile']
    scheme_prefix = get_scheme_prefix(o)
    scheme_suffix = get_scheme_suffix(o)
    codec_args = get_codec_args(o)
    scaling = get_scaling(o)
    taster = get_taster(o)
    subs_args = get_subs(o)
    dvdsubs_args = get_dvdsubs(o)
    
    OUTFILES.append(outfile)

#   ffmpeg ffargs_prefix scheme_prefix -i infile codec_args scaling scheme_suffix ffargs_suffix outfile

    ffcmd = [ FFMPEG ] + FFARGS_PREFIX + scheme_prefix + [ '-i', infile ] + \
      subs_args + dvdsubs_args + codec_args + scaling + taster + scheme_suffix + \
      FFARGS_SUFFIX + [ outfile ]

    header(outfile + ' :: ' + folder_tag + ' :: ' + file_tag)
    print('ffcmd: ' + str(ffcmd))

    if not DRY_RUN:
      subprocess.call(ffcmd)

N_FOLDERS = 0
I_FOLDER = 0
def init_count_folders():
  global N_FOLDERS, I_FOLDER
  N_FOLDERS = 0
  I_FOLDER = 0


def count_folders(target_path):
  def f():
    global N_FOLDERS
    N_FOLDERS += 1
  if os.path.isdir(target_path):
    visit_folders_depth_first(target_path, f)


def visit_folders_depth_first(target_path, f):
  subfolders = [x.path for x in os.scandir(target_path) if x.is_dir()]

  # so we can specify relative paths
  running_from = os.getcwd()
  def chdir(to):
    os.chdir(running_from)
    os.chdir(to)

  for folder in subfolders:
    print(folder)
    chdir(folder) 
    visit_folders_depth_first('.', f)

  chdir(target_path)
  f()
  os.chdir(running_from)


def visit_file(target_path, f, fargs):
  folder = os.path.dirname(target_path)

  if folder == '':
    folder = '.'
  
  # so we can specify relative paths
  running_from = os.getcwd()
  def chdir(to):
    os.chdir(running_from)
    os.chdir(to)

  chdir(folder) 
  f(fargs)
  os.chdir(running_from)


def do_it():
  init_count_folders()
  for target in TARGETS:
    count_folders(target)

  for target in TARGETS:
    if os.path.isdir(target):
      visit_folders_depth_first(target, do_convert_all_vids)
    else:
      print("target: " + target)
      basename = os.path.basename(target)
      visit_file(target, convert_vids, [basename])

def main():
  do_it()

  print("Complete. Files Output:")
  for out in OUTFILES:
    print(' :: ' + out)

