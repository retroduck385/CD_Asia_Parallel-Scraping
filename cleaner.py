import json

STRINGS_TO_REMOVE = [
    "CD Technologies Asia, Inc.",
    "cdasiaonline.com",
    "cdasia",
    "\nCD Technologies Asia, Inc.  2025", 
    "\ncdasiaonline.com\noﬃces)",
    "\ncdasiaonline.com",
    "\ncdasiaonline"
]

INPUT_FILE = "BIR_Revenue_Revenue_Memorandum_Order(2).json"
OUTPUT_FILE = "cleaned_BIR_Revenue_Revenue_Memorandum_Order(2).json"

def clean_text(text):
    if not isinstance(text, str):
        return text
    for s in STRINGS_TO_REMOVE:
        text = text.replace(s, "")
    return text

def clean_json(data):
    if isinstance(data, dict):
        return {
            key: data[key] if key == "URL" else clean_json(data[key])
            for key in data
        }
    elif isinstance(data, list):
        return [clean_json(item) for item in data]
    elif isinstance(data, str):
        return clean_text(data)
    else:
        return data

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = clean_json(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    print(f"Cleaned JSON saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
