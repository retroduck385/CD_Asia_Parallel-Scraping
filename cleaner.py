import json
from pathlib import Path
import re

# List of strings to remove from all fields except URL
STRINGS_TO_REMOVE = [
    "CD Technologies Asia, Inc.",
    "cdasiaonline.com",
    "cdasia"
    "\nCD Technologies Asia, Inc.  2025", 
    "\ncdasiaonline.com\noﬃces)",
    "\ncdasiaonline.com",
    "\ncdasiaonline"
    
]

def clean_text(text):
    """Remove lines containing any string from STRINGS_TO_REMOVE from a text string."""
    if not isinstance(text, str) or text == "":
        return text
    
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines containing any string from STRINGS_TO_REMOVE
        if any(re.search(re.escape(s), line, re.IGNORECASE) for s in STRINGS_TO_REMOVE):
            continue
        cleaned_lines.append(line)
    
    cleaned_text = "\n".join(cleaned_lines).strip()
    return cleaned_text if cleaned_text else text

def clean_dict(data, skip_url=False):
    """Recursively clean dictionary fields, skipping URL if specified."""
    if isinstance(data, dict):
        cleaned_data = {}
        for key, value in data.items():
            # Skip cleaning the URL field
            if key == "URL" and skip_url:
                cleaned_data[key] = value
            else:
                cleaned_data[key] = clean_dict(value, skip_url)
        return cleaned_data
    elif isinstance(data, list):
        return [clean_dict(item, skip_url) for item in data]
    elif isinstance(data, str):
        return clean_text(data)
    return data

def clean_json_data(json_file, output_file):
    """Clean JSON data by removing Document No and unwanted text from all fields except URL."""
    try:
        # Read the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Find the case list
        case_list = None
        for content in json_data["contents"]:
            if content["contentTitle"] == "Implementing Rules and Regulation":
                for subcontent in content["subContent"]:
                    if subcontent["subContentTitle"] == "Executive Orders":
                        case_list = subcontent["case"]
                        break
                if case_list is not None:
                    break
        
        if case_list is None:
            print("⚠️ Could not find 'Executive Orders' case list in JSON structure")
            return
        
        # Process each entry in the case list
        for entry in case_list:
            # Remove Document No: field
            if "Document No:" in entry:
                del entry["Document No:"]
            
            # Clean all fields except URL
            for key, value in entry.items():
                entry[key] = clean_dict(value, skip_url=(key == "URL"))
        
        # Write cleaned JSON to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Cleaned JSON written to: {output_file}")
    
    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file}")
    except Exception as e:
        print(f"❌ Failed to process JSON file: {e}")

def main():
    json_file = Path(__file__).parent / "scraped_output.json"
    output_file = Path(__file__).parent / "cleaned_output.json"
    clean_json_data(json_file, output_file)

if __name__ == "__main__":
    main()