# Local import
from src.states.base_state import State
from src.utils.logger import logger

class SolvingRuneState(State):
    def on_enter(self):
        self.bot.kb.set_command("none none none") # prevent kb thread intervention
        self.bot.kb.release_all_key()
        self.bot.rune_solver.reset()

    def on_exit(self):
        pass

    def check_transitions(self):
        if not self.bot.rune_solver.is_in_rune_game(
            self.bot.img_frame, self.bot.img_frame_debug):
            # Not in arrow minigame anymore
            # Stop rune detection alert and play rune solved alert
            if self.bot.cfg.get("alert", {}).get("enable", False):
                            self.bot.alert.stop_rune_alert()
            if self.bot.cfg.get("alert", {}).get("rune_solved_alert", False):
                self.bot.alert.play_rune_solved_alert()
            return "hunting"
        else:
            return None

    def on_frame(self):
        self.bot.rune_solver.solve_rune(
            self.bot.img_frame, self.bot.img_frame_debug)
