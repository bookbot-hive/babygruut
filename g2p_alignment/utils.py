import string
def insert_punctuation(original_word, syllable_word):
    # Define what we consider punctuation.
    # Here, let's treat anything that is not a letter or a dot as punctuation.
    punctuation_chars = set(ch for ch in original_word if ch not in string.ascii_letters and ch != '.')
    
    # Step 1: Identify the letter positions in the original word and record punctuation placement.
    letter_count = 0
    punctuation_map = {}  # key: letter index (0-based), value: list of punctuation marks after that letter
    
    for i, ch in enumerate(original_word):
        if ch in string.ascii_letters:
            # We've encountered a letter, increase the count
            letter_count += 1
        elif ch in punctuation_chars:
            # Punctuation appears after the last encountered letter
            # If we have no letters yet and punctuation occurs, place it at -1 index
            # meaning it goes before the first letter in the syllable version.
            insert_index = letter_count - 1
            punctuation_map.setdefault(insert_index, []).append(ch)
    
    # Step 2: Insert punctuation into the syllable_word at corresponding positions.
    # We'll build a new string from the syllable_word.
    result = []
    letter_count = 0
    for ch in syllable_word:
        result.append(ch)
        if ch in string.ascii_letters:
            # After adding this letter, check if we have punctuation to insert
            if (letter_count in punctuation_map):
                # Insert all punctuation for this letter index
                for pch in punctuation_map[letter_count]:
                    result.append(pch)
            letter_count += 1
    
    return "".join(result)

def get_phoneme_from_alignment(alignment_pairs):
    phoneme_list = []
    for pair in alignment_pairs:
        word_part, phoneme_part = pair.split('}')
        if '_' not in phoneme_part:
            if '|' in phoneme_part: 
                phoneme_part = ' '.join(phoneme_part.split('|'))
            phoneme_list.append(phoneme_part)
    return ' '.join(phoneme_list)

def get_phoneme_syllable(word: str, word_with_syll: str, phonemes: str, alignment: str) -> str:
    alignment_pairs = alignment.split(' ')
    alignment_phonemes = get_phoneme_from_alignment(alignment_pairs)
    
    # Insert punctuation into the syllable word if there is a mismatch between the word and the syllable word
    if "'" in word and "'" not in word_with_syll:
        word_with_syll = insert_punctuation(word, word_with_syll)
    
    if word.lower() != word_with_syll.replace('.', '').lower():
        raise ValueError(f"Word mismatch: '{word}' != '{word_with_syll.replace('.', '')}'")
    if phonemes != alignment_phonemes:
        raise ValueError(f"Phoneme mismatch:\nExpected: '{phonemes}'\nGot: '{alignment_phonemes}'")
    
    syllable_phonemes = []

    # Create character to phoneme mapping
    char_to_phoneme_mapping = {}
    for pair in alignment_pairs:
        word_part, phoneme_part = pair.split('}')
        if '|' in phoneme_part:
            phoneme_part = ' '.join(phoneme_part.split('|'))
            
        # Remove double word
        character = word_part.split('|')

        # if letter doesn't exist yet in the mapping, add it
        for i, char in enumerate(character):
            if i > 0:
                phoneme_part = ""
            if char not in char_to_phoneme_mapping:
                char_to_phoneme_mapping[char] = {
                    0: phoneme_part,
                    "count": 1
                }
            else:
                count = char_to_phoneme_mapping[char]["count"]
                char_to_phoneme_mapping[char][count] = phoneme_part
                char_to_phoneme_mapping[char]["count"] += 1
                
    # Map each character from the word with syllable into their respective phonemes
    char_count = {}
    for char in word_with_syll:
        if char != '.':
            char_count[char] = char_count.get(char, 0)
            if char_to_phoneme_mapping[char][char_count[char]] != '_':
                syllable_phonemes.append(char_to_phoneme_mapping[char][char_count[char]])
            char_count[char] += 1
        else:
            syllable_phonemes.append('.')
    
    return ''.join(syllable_phonemes)

if __name__ == "__main__":

    result = get_phoneme_syllable(word="abbreviate", 
                                  word_with_syll="ab.bre.vi.ate",
                                  phonemes="ə b ɹ ˈi v i ˌeɪ t", 
                                  alignment="a}ə b|b}b r}ɹ e}ˈi v}v i}i a}ˌeɪ t}t e}_")
    
    print(result)
    
    result = get_phoneme_syllable(word="where's", 
                                  word_with_syll="wheres",
                                  phonemes="w ˈɛ ɹ z", 
                                  alignment="w}w h}_ e}ˈɛ r}ɹ e}_ '|s}z")
    print(result)
