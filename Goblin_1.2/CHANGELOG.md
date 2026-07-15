# Goblin changelog v1.2 

## UI
- minors aesthetic tweaks
- replaced the dropbox for single-files and tiny button for folder by 2 egually-sized buttons.
- no more less-than-usefull messages when activating the online mode

## Functionnalities
- it is no longer possible to feed new files or folder to the waitlist while it's not empty, until a stable solution is finded.
- heartbeat-check for closed browser deactivated until fixed.
- Qwen7B and WhisperBase are now predownloaded with build.py, slower installation but smoother usage
- added rebuild script, clean and kill every process and dependencies then install and rebuild everything. Takes a few minutes. --full option to reinstall models too.
- adaptative evaluation of ETA when transcribing (still not a reliable estimation)
- adding goblin-kill alias in the installation process, call the script that kills stray goblin processes.
- changed the way Qwen14B can be dowloaded to be smoother

## Bugs
- when "nommage intelligent" is activated, goblin successfully detect the new file name, preventing it from disapearing