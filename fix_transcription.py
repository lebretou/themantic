import os
import json
import glob
import argparse
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------------------------------------
# USER CONFIGURATION
# --------------------------------------------------------------------------------

# Put your instruction prompt here. 
# You can reference the text to be corrected as {text} if you use f-strings, 
# or just append the text to this prompt.
INSTRUCTION_PROMPT = """
You are an expert transcriber. 
This interview is about asking people about their experience with LLM-based multi-agent systems.
You will receive some auto-transcribed text. There are some typos, punctuation errors, capitalization errors, word order errors, word choice errors, grammar errors, and spelling errors. 
Overall, the goal is to make the text more natural and fluent, but you should never reduce too much of the original text. Do not hallucinate or make up any information.
Instructions for the correction are as follows:
- Fix any transcription errors in the following text.
- There are also cases when speakers stutter you should remove repeated words or phrases.
- Fix any grammar errors in the following text.
- Fix any spelling errors (terms like frameworks, LLMs, etc.) in the following text.
Only output the corrected text, do not include any explanations or other text.
"""

# --------------------------------------------------------------------------------
# PIPELINE SETUP
# --------------------------------------------------------------------------------

def fix_text(client, text):
    """
    Sends the text to Claude for correction based on the INSTRUCTION_PROMPT.
    """
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001", 
            max_tokens=12000,
            messages=[
                {
                    "role": "user",
                    "content": f"{INSTRUCTION_PROMPT}\n\nText to fix:\n{text}"
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return text # Return original text on failure

def process_file(client, input_path, output_path):
    print(f"Processing {input_path} -> {output_path}")
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line_num, line in enumerate(infile, 1):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                original_text = data.get("text", "")
                
                if original_text:
                    # Fix the text using Claude
                    corrected_text = fix_text(client, original_text)
                    data["text"] = corrected_text
                    # Optional: keep original text if needed
                    # data["original_text"] = original_text
                
                # Write the updated record
                outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
                print(f"  Processed line {line_num}")
                
            except json.JSONDecodeError:
                print(f"  Skipping invalid JSON on line {line_num}")

def main():
    parser = argparse.ArgumentParser(description="Fix transcription errors in JSONL files using Claude.")
    parser.add_argument("files", nargs="*", help="Specific JSONL files to process. If empty, processes all files in input_dir.")
    parser.add_argument("--input-dir", default="merged_data", help="Directory to search for .jsonl files if no specific files are provided.")
    parser.add_argument("--output-dir", default="clean_data", help="Directory to save processed files.")
    
    args = parser.parse_args()

    # Initialize Anthropic client
    # Ensure ANTHROPIC_API_KEY is set in your environment variables
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        return

    client = Anthropic(api_key=api_key)

    output_dir = args.output_dir

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files_to_process = []
    
    if args.files:
        # Process specific files provided as arguments
        for f in args.files:
            if os.path.exists(f):
                files_to_process.append(f)
            else:
                print(f"Warning: File {f} not found. Skipping.")
    else:
        # Fallback to processing all files in input directory
        input_dir = args.input_dir
        if os.path.exists(input_dir):
            files_to_process = glob.glob(os.path.join(input_dir, "*.jsonl"))
        else:
            print(f"Error: Input directory '{input_dir}' does not exist.")
            return

    if not files_to_process:
        print("No files found to process.")
        return

    for input_path in files_to_process:
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, filename)
        process_file(client, input_path, output_path)

    print("All files processed.")

if __name__ == "__main__":
    main()

