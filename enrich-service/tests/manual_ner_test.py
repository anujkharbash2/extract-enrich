from app.ner import extract_entities

sample_text = (
    "Prime Minister Narendra Modi met with representatives from Tata Group "
    "and Infosys in New Delhi on Friday to discuss investment opportunities "
    "in Maharashtra and Karnataka."
)

entities = extract_entities(sample_text)
for e in entities:
    print(f"{e.type:15} -> '{e.text}' (chars {e.start_char}-{e.end_char})")