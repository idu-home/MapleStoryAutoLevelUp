import time

# Local import
from src.states.base_state import State
from src.utils.logger import logger

class FindingRuneState(State):
    def __init__(self, name, bot):
        super().__init__(name, bot)
        self.bot = bot
        self.is_attack = True

    def on_enter(self):
        self.bot.rune_solver.reset()
        self.disable_attack()

        if self.bot.alert:
            self.bot.alert.start_rune_alert()

    def on_exit(self):
        pass

    def disable_attack(self):
        self.is_attack = False

    def enable_attack(self):
        self.is_attack = True

    def check_transitions(self):
        # Check whether in arrow box mini game
        if self.bot.rune_solver.is_in_rune_game(
            self.bot.img_frame, self.bot.img_frame_debug):
            return "solving_rune"

        elif self.bot.rune_solver.loc_rune is not None:
            return "near_rune"

        else:
            return None

    def on_frame(self):
        # Update rune location on screen
        self.bot.rune_solver.update_rune_location(
                self.bot.img_frame,
                self.bot.img_frame_debug,
                self.bot.loc_player
        )

        # Get commend from route map
        self.bot.update_cmd_by_route()

        # Check if reach goal on route map
        self.bot.check_reach_goal()

        # If player stuck for too long, perform a random command
        if self.bot.is_player_stuck():
            self.bot.update_cmd_by_random()

        # send command to keyboard controller
        self.bot.kb.set_command(self.bot.cmd_move_x + ' ' + \
                                self.bot.cmd_move_y + ' ' + \
                                self.bot.cmd_action)
