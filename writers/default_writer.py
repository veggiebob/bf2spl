import random

from writers.writer import SPL_Writer


def _r(*args):
    coll = []
    for a in args:
        is_iter = False
        if type(a) is not str:
            try:
                for c in a:
                    coll.append(c)
                is_iter = True
            except:
                pass
        if not is_iter:
            coll.append(a)
    i = random.randint(0, len(coll) - 1)
    return coll[i]

class RandomWriter(SPL_Writer):
    def __init__(self, context_window_lines: int = 100):
        super().__init__(context_window_lines)
        self.spl_names = [
            'Achilles',
            'Fenton',
            'Macbeth',
            'Romeo',
            'Juliet',
            'Ophelia'
        ]  # todo: randomize this list

    def title(self):
        return "Boring Title."

    def character_name(self, character_id: int) -> str:
        return self.spl_names[character_id]

    def character_description(self, character_id: int):
        return "description."

    def act_description(self) -> str:
        return "act description."

    def scene_description(self) -> str:
        return "scene description."

    def noun_phrase(self, num: int) -> str:
        if num == 1:
            return "a cat"
        elif num == -1:
            return 'a ' + _r('flirt-gill', 'coward')
        elif num == 255:
            # noun phrase evaluating to 255. example:
            # rich beautiful blue clearest sweetest huge green peaceful sky
            return "the difference between the rich beautiful blue clearest sweetest huge green peaceful sky and my nose"
        else:
            raise Exception("Default writer can't create a noun phrase for the value " + num)

    def recall_fluff(self) -> str:
        return _r("your actions from the last moment.",
                  "your imminent death!")

    def simile_adj(self, inflection_hint: int=0) -> str:
        if inflection_hint > 0:
            return 'good'
        else:
            return 'horrid'