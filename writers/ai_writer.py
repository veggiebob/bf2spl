import os

import openai
import json
import requests
import datetime

from util import roman_numeral
from writers.writer import SPL_Writer

OPENAI_KEY = open('openai-key.private', 'r').readline()
openai.api_key = OPENAI_KEY

M_USER = lambda x: {'role':'user', 'content':x}
M_SYS = lambda x: {'role':'system', 'content':x}
M_ASS = lambda x: {'role':'assistant', 'content':x}

SPL_SYS_MSG =   "You are writing segments of 'code' for a programming " \
                "language known as SPL (Shakespeare Programming Language). " \
                "Reply directly and in the format given as briefly as possible, filling in words inside the {}. For example:\n" \
                "Question: Fill in the {} appropriately the following sentence:\n" \
                "'Romeo: You are as {} as a half-witted coward!'\n" \
                "Given these previous 100 lines of dialog? (dialog will be here)\n" \
                "Response: Romeo: You are as {filthy} as a half-witted coward!\n\n" \
                \
                "Note that there may be multiple {} to fill. Additionally, hints may be supplied to you " \
                "using python-style comment syntax, such as 'Romeo, {}. # a personable description " \
                "of a stack, the first of two'\n" \
                "It is ABSOLUTELY IMPERATIVE that all original content you generate is wrapped in the brackets {} as requested, like the following:\n" \
                "Query: {}. # title of the play\nResponse: {The Tragedy of Romeo and Juliet}.\n\n" \

SPL_PROMPT =    "Here is the last few lines of SPL which has been written so far:\n" \
                "CONTEXT\n" \
                "Here is the next line. Please fill in the {} appropriately in the following line:\n"

class AIResponse:
    def __init__(self, response: str, args: tuple[str], messages: list, api_response: dict):
        self.response = response
        self.args = args
        self.messages = messages
        self.api_response = api_response

class AIResponseLogger:
    def __init__(self, filename: str, dir: str=''):
        # set filename using current date and parameter
        now = datetime.datetime.now()
        filename = now.strftime('%Y-%m-%d-%H-%M-%S') + '-' + filename
        self.filename = os.path.join(dir, filename)

    def log(self, user_msg: str, ai_response: AIResponse):
        with open(self.filename, 'a') as f:
            f.write('-'*80 + '\n')
            f.write(f'User: {user_msg}\n')
            for msg in ai_response.messages[2:]:
                f.write(f'{msg["role"]}: {msg["content"]}\n')
            f.write('\nParsed args: [' + ', '.join(ai_response.args) + ']\n')

    def log_plain(self, user_msg: str, ai_response: str):
        with open(self.filename, 'a') as f:
            f.write('-'*80 + '\n')
            f.write(f'User: {user_msg}\nAI: {ai_response}\n\n')

def ask_spl(query, context: str='[No content yet]', instructions=SPL_SYS_MSG, prompt=SPL_PROMPT, *args, **kwargs) -> AIResponse:
    my_messages = [
            M_SYS(instructions),
            M_USER(prompt.replace('CONTEXT', context) + query),
        ]
    response = openai.ChatCompletion.create(
        *args,
        model='gpt-3.5-turbo',
        messages=my_messages,
        **kwargs
    )
    output = ''.join(response.choices[0].message.content)
    output_og = output
    args = []
    while '{' and '}' in output:
        i = output.index('}')
        args.append(output[output.index('{')+1:i])
        output = output[i+1:]

    return AIResponse(output_og, tuple(args), my_messages, response)

def clarify(previous_response: AIResponse, message: str, **kwargs) -> AIResponse:
    all_messages = previous_response.messages + [M_USER(message)]
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=all_messages,
        **kwargs
    )
    output = ''.join(response.choices[0].message.content)
    output_og = output
    args = []
    while '{' and '}' in output:
        i = output.index('}')
        args.append(output[output.index('{') + 1:i])
        output = output[i + 1:]

    return AIResponse(output_og, tuple(args), all_messages, response)

def ask_raw(user_msg: str, **kwargs) -> str:
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            M_USER(user_msg)
        ],
        **kwargs
    )
    return ''.join(response.choices[0].message.content)


def cache(section: str):
    def f_gen(func):
        def wrapper(self, *args, **kwargs):
            if section not in self.cache:
                self.cache[section] = {}
            if tuple(args) not in self.cache[section]:
                self.cache[section][args] = func(self, *args, **kwargs)
            return self.cache[section][args]
        return wrapper
    return f_gen

def end_punc(f):
    """
    Ensure a function produces output that ends with punctuation.
    :param f:
    :return:
    """
    def wrapper(self, *args, **kwargs):
        response = f(self, *args, **kwargs)
        if response[-1] not in ['.', '!']:
            response += '.'
        return response
    return wrapper

class ChatGptWriter(SPL_Writer):
    def __init__(self, context_window_lines: int = 10, temp=0.3, logger:AIResponseLogger=None):
        super().__init__(context_window_lines)
        self.logger = logger
        self.temp = temp
        self.topic = self.ask_raw('What should the topic of this play be? Be short and descriptive. For example, '
                             '"A whimsical comedy set in a quaint bakery where the arrival of a mysterious batch '
                             'of enchanted muffins causes chaos and hilarity among the townsfolk"')
        self.cache = {}
        self.characters = {}

    def ask_raw(self, query: str, **kwargs) -> str:
        response = ask_raw(query, temperature=self.temp, **kwargs)
        if self.logger is not None:
            self.logger.log_plain(query, response)
        return response

    def ask_with_response(self, query: str, expected_args: int=0, **kwargs) -> AIResponse:
        response = ask_spl(query, self.script_buffer + '\n\nThe topic of this play is: ' + self.topic,
                       temperature=self.temp, **kwargs)
        if len(response.args) < expected_args:
            response = clarify(response, 'Please ensure to use {} around all responses. There are %d required.'%expected_args)
        if self.logger is not None:
            self.logger.log(query, response)
        return response

    def ask(self, query: str, expected_args: int=0, **kwargs) -> tuple[str]:
        return self.ask_with_response(query, expected_args, **kwargs).args

    @cache('title')
    @end_punc
    def title(self) -> str:
        return self.ask('{}. # title of the play')[0]

    @cache('character_name')
    def character_name(self, character_id: int) -> str:
        if len(self.characters) == 0:
            num_characters = 5
            inputs = ', '.join(["{}" for _ in range(num_characters)])
            characters = self.ask('Names of Shakespearean characters to use in this play: ' + inputs)
            self.characters = {i: characters[i] for i in range(num_characters)}
        return self.characters[character_id]

    @cache('character_description')
    @end_punc
    def character_description(self, c_id: int) -> str:
        return self.ask(self.character_name(c_id) + ', {}. # fruitful description of this character')[0]

    @end_punc
    def act_description(self) -> str:
        return self.ask('Act ' + roman_numeral(self.current_act) + ': {}. # act description')[0]

    @end_punc
    def scene_description(self) -> str:
        return self.ask('Scene ' + roman_numeral(self.current_scene) + ': {}. # scene description')[0]

    def noun_phrase(self, num: int) -> str:
        if num == 1:
            return "a cat"
        elif num == -1:
            return 'a ' + 'coward'
        elif num == 255:
            # noun phrase evaluating to 255. example:
            # rich beautiful blue clearest sweetest huge green peaceful sky
            return "the difference between the rich beautiful blue clearest sweetest huge green peaceful sky and my nose"
        else:
            raise Exception("Default writer can't create a noun phrase for the value " + num)

    @end_punc
    def recall_fluff(self) -> str:
        fluff = self.ask('Recall {} # anything appropriate!')[0]
        return f'Recall {fluff}'

    def simile_adj(self, inflection_hint: int = 0) -> str:
        return self.ask('I am as {} as ...')[0]

