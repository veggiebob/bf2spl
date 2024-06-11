# BF2SPL

## About
Translator from 
[brainf*ck](https://esolangs.org/wiki/Brainfuck) to [Shakespeare Programming Language](https://esolangs.org/wiki/Shakespeare)

## Modes

### Boring Mode
A little bit random, mostly the same. Always produces a correct program.

### AI Mode
Uses ChatGPT to fill in descriptions, adjectives, noun phrases, etc.
Usually produces a 'correct' program, but the definition of correctness changes based on the SPL implementation (nouns/adjectives available).
Word list validation coming soon!

## Running

Python >= 3.10  
Input BF accepts all BF with matching brackets.

### Boring Mode
```sh
python bf2spl.py < input_bf.b
```

### AI Mode
You must create a `openai-key.private` file in the root directory, with the api key inside on the first line.
```sh
python bf2spl.py ai < input_bf.b
```
