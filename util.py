
R_NUMERALS = [
    ('M', 1000),
    ('D', 500),
    ('C', 100),
    ('L', 50),
    ('X', 10),
    ('V', 5),
    ('I', 1)
]


def roman_numeral(num: int) -> str:
    s = ''
    i = 0
    while i < len(R_NUMERALS):
        symbol, value = R_NUMERALS[i]
        p = ((i + 1) % 2) + 1
        if num < value:
            symbol2, value2 = R_NUMERALS[i + p]
            if num >= (value - value2):
                i = 0
                s += symbol2 + symbol
                num -= value - value2
        if num >= value:
            s += symbol
            num -= value
            i = 0
        else:
            i += 1
        if num == 0:
            break
    return s