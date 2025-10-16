def convert_layout_mixed(text: str) -> str:
    """
    Converts a string between Russian and English keyboard layouts.
    Useful for correcting user input typed in the wrong layout.

    :param text: Input text to convert.
    :return: Converted text with swapped keyboard layout.
    """
    ru_dict = (
        "йцукенгшщзхъфывапролджэячсмитьбюёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ"
    )
    en_dict = (
        "qwertyuiop[]asdfghjkl;'zxcvbnm,.`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>~"
    )
    # Dictionaries for transliteration between layouts
    eng_to_rus = str.maketrans(en_dict, ru_dict)
    rus_to_eng = str.maketrans(ru_dict, en_dict)

    # Convert each character by checking both layouts
    result = ""
    for char in text:
        if char in en_dict:
            result += char.translate(eng_to_rus)
        elif char in ru_dict:
            result += char.translate(rus_to_eng)
        else:
            result += char

    return result
