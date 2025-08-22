from src.states.base_state import State

class HuntingState(State):
    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def check_transitions(self):
        # Performance: Start rune detection profiling
        self.bot.profiler.mark("Hunting - Rune Detection Start")
        
        if self.bot.rune_solver.is_rune_enable(
            self.bot.img_frame_gray, self.bot.img_frame_debug) or \
            self.bot.rune_solver.is_rune_warning(
            self.bot.img_frame_gray, self.bot.img_frame_debug):
            # When "Rune enable" message appears on screen
            self.bot.screenshot_img_frame()

            self.bot.profiler.mark("Hunting - Rune Detection Found")
            return "finding_rune"

        else:
            self.bot.profiler.mark("Hunting - Rune Detection Complete")
            return None

    def on_frame(self):
        # Performance: Start hunting frame profiling
        self.bot.profiler.mark("Hunting - Frame Start")
        
        # Get commend from route map
        self.bot.update_cmd_by_route()
        self.bot.profiler.mark("Hunting - Route Command")

        # Check if reach goal on route map
        self.bot.check_reach_goal()
        self.bot.profiler.mark("Hunting - Goal Check")

        # Get attack commend by detecting mobs near players
        self.bot.update_cmd_by_mob_detection()
        self.bot.profiler.mark("Hunting - Mob Detection")

        # If player stuck for too long, perform a random command
        if self.bot.is_player_stuck():
            self.bot.update_cmd_by_random()
        self.bot.profiler.mark("Hunting - Stuck Check")

        # send command to keyboard controller
        self.bot.kb.set_command(self.bot.cmd_move_x + ' ' + \
                                self.bot.cmd_move_y + ' ' + \
                                self.bot.cmd_action)
        self.bot.profiler.mark("Hunting - Command Send")
