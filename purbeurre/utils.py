def get_words_from_sentence(sentence):
    """Get words from sentence."""
    cursor, i, sentence = 0, 0, sentence.strip().lower() + " "

    while i <= len(sentence) - 1:
        if sentence[i] in (' ', '\n', ',', '.', ')', ']',
                           ';', '!', '?', '_', '/', ':'):
            if i - 1 >= cursor:
                word = sentence[cursor:i]
                if "'" in word:
                    word = word[word.index("'") + 1:]
                yield word
            delta = 1
            while i + delta <= len(sentence) - 1:
                if sentence[i + delta] not in (' ', '\n', ',', '.', '?', '!',
                                               '[', ']', '(', ')', ';',
                                               '_', '/', ':'):
                    break
                delta += 1
            i = cursor = i + delta
        i += 1
