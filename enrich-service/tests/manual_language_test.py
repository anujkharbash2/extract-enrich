from app.language import detect_language

samples = {
    "english": "The quick brown fox jumps over the lazy dog near the riverbank.",
    "hindi": "यह एक परीक्षण वाक्य है जो हिंदी भाषा में लिखा गया है।",
    "tamil": "இது தமிழ் மொழியில் எழுதப்பட்ட ஒரு சோதனை வாக்கியம்.",
    "bengali": "এটি বাংলা ভাষায় লেখা একটি পরীক্ষামূলক বাক্য।",
    "marathi": "हे मराठी भाषेत लिहिलेले एक चाचणी वाक्य आहे.",
}

for label, text in samples.items():
    result = detect_language(text)
    print(f"{label:10} -> detected={result.language_code:5} confidence={result.confidence:8} target={result.is_target_language}")