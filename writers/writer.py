class SPL_Writer:
    def __init__(self, context_window_lines: int = 100):
        self.context_window_lines = context_window_lines
        self.script_buffer = ''  # in progress script, optionally used for context
        self.current_act = None  # updated by Play
        self.current_scene = None  # updated by Play
        pass

    def _buf_append(self, newstuff: str):
        self.script_buffer += newstuff
        if newstuff.endswith('\n') and self.script_buffer.count('\n') > self.context_window_lines:
            self.script_buffer = self.script_buffer[self.script_buffer.find('\n') + 1:]

    def _clear_buffer(self):
        self.script_buffer = ''

    def title(self) -> str:
        """Must end with a period"""
        pass

    def character_name(self, character_id: int) -> str:
        """Must be an actual Shakespeare character"""
        pass

    def character_description(self, character_id: int) -> str:
        """Must end with a period"""
        pass

    def act_description(self) -> str:
        """Must end with a period"""
        pass

    def scene_description(self) -> str:
        """Must end with a period"""
        pass

    def noun_phrase(self, num: int) -> str:
        """
        Begins with an article, if necessary?
        Expression that evaluates to `num`. Does not need to end with a period.
        Minimally, only needs to support 255, -1, and 1
        """
        pass

    def recall_fluff(self) -> str:
        """Fluff following 'Recall' in a recall statement. MUST end with punctuation."""
        pass

    def simile_adj(self, inflection_hint: int = 0) -> str:
        """
        Return a single adjective which is usually placed between 2 'as' words.
        Example: 'Are you as good as I?' where 'good' would be the adjective.
        `inflection_hint` is given to signal a relatively positive or negative adjective,
        but it doesn't matter, so it's not necessary.
        """
        pass
