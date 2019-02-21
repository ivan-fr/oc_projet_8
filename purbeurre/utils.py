def get_words_from_sentence(sentence):
    """Get words from sentence."""
    cursor, i, sentence = 0, 0, sentence.strip().lower() + " "

    while i <= len(sentence) - 1:
        if not sentence[i].isalpha() and not sentence[i] == "'":
            if i - 1 >= cursor:
                word = sentence[cursor:i]
                if "'" in word:
                    word = word[word.index("'") + 1:]
                yield word
            delta = 1
            while i + delta <= len(sentence) - 1:
                if sentence[i + delta].isalpha():
                    break
                delta += 1
            i = cursor = i + delta
        i += 1


def wash_product(product: dict):
    # wash categories keys
    if product.get('categories_hierarchy'):
        i = 0
        while i <= len(product['categories_hierarchy']) - 1:
            if ':' in product['categories_hierarchy'][i]:
                product['categories_hierarchy'][i] = \
                    (product['categories_hierarchy'][i].split(':'))[1]
            i += 1
    if product.get('categories'):
        product['categories'] = product['categories'].split(',')
        i = 0
        while i <= len(product['categories']) - 1:
            if ':' in product['categories'][i]:
                product['categories'][i] = \
                    (product['categories'][i].split(':'))[1]
            i += 1
    # wash ingredients keys
    if product.get('ingredients_text_fr', None):
        product['ingredients_text_fr'] = (
            ' '.join(get_words_from_sentence(ingredient)) for ingredient
            in
            product['ingredients_text_fr'].split(','))
    else:
        product['ingredients'] = (
            ' '.join(get_words_from_sentence(ingredient['text'])) for
            ingredient
            in product.get('ingredients', ()))
    return product
