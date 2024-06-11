"""
Author: Jacob Bowman
CHANGELOG

## 2.1.1
- moved to personal computer

## 2.1.0
- improved Writer API
- fixed wrapping negative numbers and stack manipulation

## 2.0.0
- copied from bf2spl_2.0.txt
"""
import sys
import random

from util import roman_numeral
from writers.writer import SPL_Writer

# https://web.archive.org/web/20220721085340/http://shakespearelang.sourceforge.net/report/shakespeare/shakespeare.html
I_LEFT = '<'
I_RIGHT = '>'
I_INC = '+'
I_DEC = '-'
I_JMP_BGN = '['
I_JMP_END = ']'
I_IN = ','
I_OUT = '.'

VALID_BF_SYMBOLS = {
    I_LEFT,
    I_RIGHT,
    I_INC,
    I_DEC,
    I_JMP_BGN,
    I_JMP_END,
    I_IN,
    I_OUT
}

def find_matching(instructions, index):
    inst = instructions
    if inst[index] == I_JMP_BGN:
        depth = 1
        for i in range(index + 1, len(inst)):
            if inst[i] == I_JMP_END:
                depth -= 1
                if depth == 0:
                    return i
            elif inst[i] == I_JMP_BGN:
                depth += 1
        return -1
    elif inst[index] == I_JMP_END:
        depth = 1
        for i in reversed(range(0, index)):
            if inst[i] == I_JMP_END:
                depth += 1
            elif inst[i] == I_JMP_BGN:
                depth -= 1
                if depth == 0:
                    return i
        return -1
    else:
        raise Exception("Can't find a matching \"%s\"" % inst[index])


def consume(f, f_out):
    def wrapper(*args, **kwargs):
        result = f(*args, **kwargs)
        f_out(result)
        return result

    return wrapper



class SPL_Formatter:
    def __init__(self, play):
        self.play = play

    def enter(self, *character_ids) -> str:
        names = ' and '.join(list(map(self.play.get_name, character_ids)))
        return "[Enter " + names + "]\n"

    def exit(self, *character_ids) -> str:
        if len(character_ids) == 0:
            return "[Exeunt]\n"
        verb = "Exit" if len(character_ids) == 1 else "Exeunt"
        names = ' and '.join(list(map(self.play.get_name, character_ids)))
        return "[" + verb + " " + names + "]\n"

    def line(self, character_id: int, message: str, *messages) -> str:
        return self.play.get_name(character_id) + ': ' + message + ''.join(messages) + '\n'

    def act(self, act_num: int) -> str:
        return f'\nAct {roman_numeral(act_num)}: ' + self.play.writer.act_description() + '\n'

    def scene(self, scene_num: int) -> str:
        return f'Scene {roman_numeral(scene_num)}: ' + self.play.writer.scene_description() + '\n\n'


# SPL Play
ZERO_ID = 0
LEFT_STACK_ID = 1
CURSOR_ID = 2
RIGHT_STACK_ID = 3
CHARACTER_CONTROL_ID = 4


class Play:
    def __init__(self, instructions: str, writer: SPL_Writer):
        self.instructions = instructions

        self.writer = writer
        self.spl_formatter = SPL_Formatter(self)
        self.characters = {}  # character_id(int) -> name(str)
        # note: the first scene of an act has the same index as the act
        self.acts = {}  # index: act #
        self.scenes = {}  # index: scene #

        self.jumps = {}  # from index: to index
        # optimizations
        self.ignore = set()  # instructions to ignore

        # setup
        self._establish_jumps()

    def _establish_jumps(self):
        # first pass: set up all regular jumps
        start_bracket_idx = []
        bracket_depth = {}  # index -> depth ... highest level is 0
        for i in range(len(self.instructions)):
            inst = self.instructions[i]
            if inst == I_JMP_BGN:
                bracket_depth[i] = len(start_bracket_idx)
                start_bracket_idx.append(i)
            elif inst == I_JMP_END:
                if len(start_bracket_idx) == 0:
                    raise Exception("Unmatched ']' at index " + i)
                og_idx = start_bracket_idx.pop()
                self.jumps[i] = og_idx
                self.jumps[og_idx] = i
                bracket_depth[i] = len(start_bracket_idx)

        # finally establish acts and scenes
        dests = sorted(self.jumps.values())
        act = 2  # introductions happen in Act I
        scene = 2
        for d in dests:
            if bracket_depth[d] == 0:
                self.acts[d] = act
                self.scenes[d] = 1
                act += 1
                scene = 2
            else:
                self.scenes[d] = scene
                scene += 1

    def _reassign_jump_dest(self, og_idx: int, new_idx: int):
        for k in self.jumps:
            if self.jumps[k] == og_idx:
                self.jumps[k] = new_idx

    def get_name(self, id: int):
        if id not in self.characters:
            self.characters[id] = self.writer.character_name(id)
        return self.characters[id]

    def dramatis_personae(self):
        output = ""
        for ch in [ZERO_ID, CURSOR_ID, LEFT_STACK_ID, RIGHT_STACK_ID, CHARACTER_CONTROL_ID]:
            output += self.get_name(ch) + ', ' + self.writer.character_description(ch) + '\n'
        return output

    def character_introduction(self):
        """
        Assigns both stack characters a value of -1 (or any neg num)
        so that we know when the stack is empty.
        -1 is not a possible value in BF; it wraps to 255 instead.
        So, this should be a complete impl.
        """
        output = ''

        def feed(s):
            nonlocal output
            output += s

        spl = self.spl_formatter
        enter = consume(spl.enter, feed)
        exit = consume(spl.exit, lambda s: feed(s + '\n'))
        line = consume(spl.line, lambda s: feed('\t' + s))
        w = self.writer

        feed(spl.act(1))
        feed(spl.scene(1))
        enter(LEFT_STACK_ID, RIGHT_STACK_ID)
        line(LEFT_STACK_ID, f'Thou art {w.noun_phrase(-1)}. Remember yourself!')
        line(RIGHT_STACK_ID, f'Thou art {w.noun_phrase(-1)}. Remember yourself!')
        exit()

        return output

    def statement(self, index: int) -> str:
        """
        Translates a single BF character into SPL.
        """
        # optimizations (ignores)
        if index in self.ignore:
            return ''

        output = ""
        inst = self.instructions[index]

        # save myself some time
        spl = self.spl_formatter

        def feed(s):
            nonlocal output
            output += s

        enter = consume(spl.enter, feed)
        exit = consume(spl.exit, lambda s: feed(s + '\n'))
        line = consume(spl.line, lambda s: feed('\t' + s))
        w = self.writer

        # if this is the start of a scene or act, the header should
        # be prepended to the output appropriately.
        new_act_scene = False
        header = ''
        if index in self.acts:
            feed(spl.act(self.acts[index]))
        if index in self.scenes:
            feed(spl.scene(self.scenes[index]))
            if index in self.jumps.values():
                enter(CHARACTER_CONTROL_ID)
                exit()

        # assign new value ('+' and '-')
        if inst == I_INC or inst == I_DEC:
            # enter any stack character and the cursor
            enter(ZERO_ID, CURSOR_ID)

            # [either stack character]: You are as [adjective] as the sum of thyself and (noun phrase)
            positive = inst == I_INC
            sign = 1 if positive else -1
            noun_phrase = w.noun_phrase(sign)
            line(ZERO_ID, f'You are as {w.simile_adj(sign)} as the sum of thyself and {noun_phrase}.')

            # check to see if 0 - wrap around
            if inst == I_DEC:
                line(CURSOR_ID, f'Am I worse than you?')
                noun_phrase = w.noun_phrase(255)
                line(ZERO_ID, f'If so, you are {noun_phrase}.')

            # exeunt
            exit()

        # output a value ('.')
        if inst == I_OUT:
            # enter the cursor and any other
            enter(ZERO_ID, CURSOR_ID)
            # [any character]: Speak your mind!
            line(ZERO_ID, "Speak your mind!")
            # exeunt
            exit()

        # input a value (',')
        if inst == I_IN:
            # enter the cursor and any other
            enter(CURSOR_ID, ZERO_ID)
            # [any other]: Open your mind.
            line(ZERO_ID, "Open your mind.")
            # if the input is -1, change it to 0 for BF
            line(CURSOR_ID, f"Am I as {w.simile_adj(-1)} as {w.noun_phrase(-1)}?")
            line(ZERO_ID, f"If so, you are as {w.simile_adj(-1)} as I.")
            # exeunt
            exit()

        # manipulate stack (> and <)
        # >
        # this one is longer because the stack has to auto-expand
        if inst == I_RIGHT:
            # enter left stack and cursor
            enter(LEFT_STACK_ID, CURSOR_ID)
            # [cursor]: Remember me.
            line(CURSOR_ID, "Remember me.")
            # exit left stack
            exit(LEFT_STACK_ID)
            # enter right stack
            enter(RIGHT_STACK_ID)
            # pop right stack
            line(CURSOR_ID, f"Recall {w.recall_fluff()}")
            # exit cursor
            exit(CURSOR_ID)
            enter(ZERO_ID)
            line(RIGHT_STACK_ID, "Am I worse than you?")
            line(ZERO_ID, "If so, remember yourself.")
            line(RIGHT_STACK_ID, "Am I worse than you?")
            line(ZERO_ID, f"If so, you are as {w.simile_adj(1)} as I.")
            exit(ZERO_ID)
            # cursor = right stack
            enter(CURSOR_ID)
            line(RIGHT_STACK_ID, f"You are as {w.simile_adj(1)} as I.")
            # exeunt
            exit()

        # <
        if inst == I_LEFT:
            # enter right stack and cursor
            enter(RIGHT_STACK_ID, CURSOR_ID)
            # [cursor]: Remember me.
            line(CURSOR_ID, 'Remember me.')
            # exit right stack
            exit(RIGHT_STACK_ID)
            # enter left stack
            enter(LEFT_STACK_ID)
            # [cursor]: Recall [fluff]
            line(CURSOR_ID, f'Recall {w.recall_fluff()}')
            # [left stack]: You are as [adj] as I.
            line(LEFT_STACK_ID, f'You are as {w.simile_adj(1)} as I.')
            # exeunt
            exit()

        # goto ('[' and ']')

        # we are assuming that all gotos have been pre-calculated
        # we can only jump to a scene within our act, or another act
        #  (not another scene in another act)
        # if it's a '[':
        if inst == I_JMP_BGN:
            #   enter ZERO character and cursor
            enter(ZERO_ID, CURSOR_ID)
            #   [ZERO]: Am I as good as you?
            line(ZERO_ID, f'Am I as {w.simile_adj(1)} as you?')
            exit(ZERO_ID)
            #   [cursor]: If so, let us proceed to [appropriate act or scene]
            dest = self.jumps[index]
            if dest in self.acts:
                line(CURSOR_ID, 'If so, let us proceed to Act ' + roman_numeral(self.acts[dest]) + '.')
            elif dest in self.scenes:
                line(CURSOR_ID, 'If so, let us proceed to Scene ' + roman_numeral(self.scenes[dest]) + '.')
            #   exeunt
            exit()
        # if it's a ']':
        if inst == I_JMP_END:
            #   enter ZERO character and cursor
            enter(ZERO_ID, CURSOR_ID)
            #   [ZERO]: Am I not as good as you?
            line(ZERO_ID, f'Am I not as {w.simile_adj(1)} as you?')
            exit(ZERO_ID)
            #   [cursor]: If so, we shall return to [appropriate act or scene]
            dest = self.jumps[index]
            if dest in self.acts:
                line(CURSOR_ID, 'If so, we shall return to Act ' + roman_numeral(self.acts[dest]) + '.')
            elif dest in self.scenes:
                line(CURSOR_ID, 'If so, we shall return to Scene ' + roman_numeral(self.scenes[dest]) + '.')
            #   exeunt
            exit()

        return output

    def render_spl(self) -> str:
        output = ''

        self.writer._clear_buffer()

        def write(s: str):
            nonlocal output
            output += s
            self.writer._buf_append(s)

        self.writer.current_act = 1
        self.writer.current_scene = 1

        write(self.writer.title() + '\n\n')
        write(self.dramatis_personae() + '\n')

        write(self.character_introduction())
        for i in range(len(self.instructions)):
            if i in self.acts:
                self.writer.current_act = self.acts[i]
            if i in self.scenes:
                self.writer.current_scene = self.scenes[i]
            write(self.statement(i))

        # print('jumps', self.jumps, file=sys.stderr)
        # print('acts', self.acts, file=sys.stderr)
        # print('scenes', self.scenes, file=sys.stderr)

        return output


def valid(bf_symbol) -> bool:
    return bf_symbol in VALID_BF_SYMBOLS


def filter_bf(bf: str) -> bool:
    return ''.join([c for c in bf if valid(c)])


if __name__ == '__main__':
    cmd_args = sys.argv[1:]
    if 'ai' in [arg.lower() for arg in cmd_args]:
        from writers.ai_writer import ChatGptWriter, AIResponseLogger
        logger = AIResponseLogger('bf2spl-log.txt', dir='logs')
        writer = ChatGptWriter(logger=logger)
    else:
        from writers.default_writer import RandomWriter
        writer = RandomWriter()
    bf = ''
    for line in sys.stdin:
        bf += filter_bf(line)
    play = Play(bf, writer=writer)
    print(play.render_spl())