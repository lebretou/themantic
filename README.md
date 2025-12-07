# Thematic Scripts for Analyzing MAS interviews
## Preprocess scripts
Use `vtt_process.py` to process the raw data from auto-transcibed Zoom recordings into `JSONL` format.
Use `fix_transcription.py` to further clean (fix spelling, remove stutters) in the scripts.

## Web interface to visualize the interview scripts
Use `index.html` inside the `web_interface` folder to visualize interviews. Simply open this file in your browers and load `{participant_id}.jsonl` from the folder `clean_data`.
