import re


class TextProcessor:
    @staticmethod
    def clean_punctuation(text: str) -> str:
        """
        Fixes spacing around punctuation marks.
        Example: "word , word" -> "word, word"
        """
        # Remove space before comma, period, colon, semicolon, exclamation,
        # question, closing paren/quote
        text = re.sub(r'\s+([.,:;?!»)])', r'\1', text)

        # Remove space after opening paren/quote
        text = re.sub(r'([«(])\s+', r'\1', text)
        return text.strip()

    @staticmethod
    def format_word_sequence(words: list) -> str:
        """
        Joins words from the RNC JSON structure, applying bold formatting to hits.
        """
        text_parts = []
        for word in words:
            token_text = word.get("text", "")
            is_hit = word.get("displayParams", {}).get("hit", False)

            if is_hit:
                token_text = f"**{token_text}**"

            text_parts.append(token_text)

        # Join with spaces first, then clean up punctuation
        raw_text = " ".join(text_parts)
        return TextProcessor.clean_punctuation(raw_text)
