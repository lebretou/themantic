import json
import os
import glob
import argparse
import webvtt

def get_role(name):
    """
    Map speaker name to role.
    Zhongzheng Xu -> Interviewer
    Others -> Participant
    """
    if name.strip() == "Zhongzheng Xu":
        return "Interviewer"
    return "Participant"

def process_vtt_file(file_path, output_dir):
    try:
        # Determine output filename
        filename = os.path.basename(file_path)
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(output_dir, f"{stem}.jsonl")
        
        captions = webvtt.read(file_path)
        
        utterances = []
        current_speaker_name = None
        current_text_parts = []
        
        for caption in captions:
            text = caption.text.strip()
            # Handle newlines within a single caption payload by replacing with space
            text = text.replace('\n', ' ')
            
            # Try to extract speaker from the text line (Format: "Speaker: Text")
            # We look for the first colon
            if ':' in text:
                parts = text.split(':', 1)
                speaker_candidate = parts[0].strip()
                content = parts[1].strip()
                
                # Simple heuristic: Speaker names shouldn't be too long. 
                # If strict format is guaranteed, this is fine.
                speaker_name = speaker_candidate
            else:
                # No colon found, treat as continuation of previous speaker
                speaker_name = current_speaker_name
                content = text

            if speaker_name is None:
                # Skip if we haven't found a speaker yet
                continue

            # Merge consecutive utterances from the same speaker
            if speaker_name == current_speaker_name:
                current_text_parts.append(content)
            else:
                # New speaker found. Save the previous utterance if it exists.
                if current_speaker_name is not None:
                    role = get_role(current_speaker_name)
                    full_text = " ".join(current_text_parts)
                    utterance = {
                        "speaker": role,
                        "text": full_text
                    }
                    utterances.append(utterance)
                
                # Start tracking the new speaker
                current_speaker_name = speaker_name
                current_text_parts = [content]
        
        # Append the last utterance after the loop
        if current_speaker_name is not None and current_text_parts:
            role = get_role(current_speaker_name)
            full_text = " ".join(current_text_parts)
            utterance = {
                "speaker": role,
                "text": full_text
            }
            utterances.append(utterance)
            
        # Write to JSONL output file
        with open(output_path, 'w', encoding='utf-8') as f:
            for utt in utterances:
                f.write(json.dumps(utt, ensure_ascii=False) + '\n')
                
        print(f"Processed {filename} -> {os.path.basename(output_path)}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process VTT files to JSONL.")
    parser.add_argument("inputs", nargs="*", help="Input files or directories to process.")
    parser.add_argument("--output-dir", default="merged_data", help="Directory to save processed files.")

    args = parser.parse_args()

    output_dir = args.output_dir
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    files_to_process = []
    
    if args.inputs:
        for path in args.inputs:
            if os.path.isfile(path):
                files_to_process.append(path)
            elif os.path.isdir(path):
                files_to_process.extend(glob.glob(os.path.join(path, "*.vtt")))
            else:
                print(f"Warning: {path} does not exist. Skipping.")
    else:
        # Default behavior: process raw_data
        input_dir = "raw_data"
        if os.path.exists(input_dir):
            files_to_process = glob.glob(os.path.join(input_dir, "*.vtt"))
        else:
            print(f"Default input directory '{input_dir}' not found.")
            return

    if not files_to_process:
        print("No .vtt files found to process.")
        return

    print(f"Found {len(files_to_process)} files to process.")
    for vtt_file in files_to_process:
        process_vtt_file(vtt_file, output_dir)

if __name__ == "__main__":
    main()

