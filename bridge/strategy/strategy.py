"""High-level strategy code"""

# !v DEBUG ONLY
import math  # type: ignore  # noqa: F401
from time import time  # type: ignore  # noqa: F401
from typing import Optional
from random import randint

from bridge import const
from bridge.auxiliary import aux, fld, rbt  # type: ignore  # noqa: F401
from bridge.const import State as GameStates
from bridge.router.actions import (  # type: ignore  # noqa: F401
    Action,
    Actions,
    KickActions,
    StrategyActions,
)


class Strategy:
    """Main class of strategy"""

    def __init__(
        self,
    ) -> None:
        self.we_active = False
        self.prev_ball = aux.Point(0, 0)

    def process(self, field: fld.Field) -> list[Optional[Action]]:
        """Game State Management"""
        if field.game_state not in [GameStates.KICKOFF, GameStates.PENALTY]:
            if field.active_team in [const.Color.ALL, field.ally_color]:
                self.we_active = True
            else:
                self.we_active = False

        actions: list[Optional[Action]] = []
        for _ in range(const.TEAM_ROBOTS_MAX_COUNT):
            actions.append(None)

        match field.game_state:
            case GameStates.RUN:
                self.run(field, actions)
            case GameStates.TIMEOUT:
                pass
            case GameStates.HALT:
                return [None] * const.TEAM_ROBOTS_MAX_COUNT
            case GameStates.PREPARE_PENALTY:
                pass
            case GameStates.PENALTY:
                pass
            case GameStates.PREPARE_KICKOFF:
                pass
            case GameStates.KICKOFF:
                pass
            case GameStates.FREE_KICK:
                pass
            case GameStates.STOP:
                # The router will automatically prevent robots from getting too close to the ball
                self.run(field, actions)
            case GameStates.BALL_PLACEMENT:
                pass
            case GameStates.DEBUG:
                pass

        return actions

    def run(self, field: fld.Field, actions: list[Optional[Action]]) -> None:
        """
        ONE ITERATION of strategy
        NOTE: robots will not start acting until this function returns an array of actions,
              if an action is overwritten during the process, only the last one will be executed)

        Examples of getting coordinates:
        - field.allies[8].get_pos(): aux.Point -   coordinates  of the 8th  robot from the allies
        - field.enemies[14].get_angle(): float - rotation angle of the 14th robot from the opponents

        - field.ally_goal.center: Point - center of the ally goal
        - field.enemy_goal.hull: list[Point] - polygon around the enemy goal area


        Examples of robot control:
        - actions[2] = Actions.GoToPoint(aux.Point(1000, 500), math.pi / 2)
                The robot number 2 will go to the point (1000, 500), looking in the direction π/2 (up, along the OY axis)

        - actions[3] = Actions.Kick(field.enemy_goal.center)
                The robot number 3 will hit the ball to 'field.enemy_goal.center' (to the center of the enemy goal)

        - actions[9] = Actions.BallGrab(0.0)
                The robot number 9 grabs the ball at an angle of 0.0 (it looks to the right, along the OX axis)
        """
        active_robots: list[int] = []
        for i in range(16):
            if field.allies[i].is_used():
                active_robots.append(i)
        
        if len(active_robots) > 0:
            gk_id = active_robots[0]
            self.goalkeeper(field=field,actions=actions, idx=gk_id)
        ball = field.ball.get_pos()

        if len(active_robots) > 2:
            attk_id = active_robots[1]
            actions[active_robots[2]] = Actions.Stop()
            #Attacker
            self.attacker(field, actions, gk_id, attk_id)
        
    def goalkeeper(self, field: fld.Field, actions: list[Optional[Action]], idx: int):
        ball = field.ball.get_pos()
        if ball.x - self.prev_ball.x != 0:
            if field.ball.get_vel().mag() > 2.0:
                k = (ball.y - self.prev_ball.y) / (ball.x - self.prev_ball.x)

                if field.ally_color == const.Color.BLUE:
                    y = self.prev_ball.y - k * self.prev_ball.x + k * (field.ally_goal.center.x + 100)
                    if y >= field.ally_goal.up.y and y <= field.ally_goal.down.y:
                        # field.strategy_image.draw_circle(aux.Point(field.ally_goal.center.x + 100, y), size_in_mms = 100)  
                        ang = (field.ball.get_pos() - field.allies[idx].get_pos()).arg()
                        actions[idx] = Actions.GoToPointIgnore(aux.Point(field.ally_goal.center.x + 100, y), ang)  
                else: 
                    y = self.prev_ball.y - k * self.prev_ball.x + k * (field.ally_goal.center.x - 100)
                    if y <= field.ally_goal.up.y and y >= field.ally_goal.down.y:
                        # field.strategy_image.draw_circle(aux.Point(field.ally_goal.center.x + 100, y), size_in_mms = 100)   
                        ang = (field.ball.get_pos() - field.allies[idx].get_pos()).arg()
                        actions[idx] = Actions.GoToPointIgnore(aux.Point(field.ally_goal.center.x - 100, y), ang)
        self.prev_ball = ball
    def attacker(self, field: fld.Field, actions: list[Optional[Action]], idx_gk: int, idx_at: int):
        goal_max_y = 350
        if field.allies[idx_at].get_pos().x - field.allies[idx_gk].get_pos().x != 0:
            k_up = (field.allies[idx_at].get_pos().y - field.allies[idx_gk].get_pos().y - 100) / (field.allies[idx_at].get_pos().x - field.allies[idx_gk].get_pos().x)
            b_up = field.allies[idx_at].get_pos().y - k_up * field.allies[idx_at].get_pos().x
            k_down = (field.allies[idx_at].get_pos().y - field.allies[idx_gk].get_pos().y + 100) / (field.allies[idx_at].get_pos().x - field.allies[idx_gk].get_pos().x)
            b_down = field.allies[idx_at].get_pos().y - k_down * field.allies[idx_at].get_pos().x
            y_kick_up = k_up * 2250 + b_up
            y_kick_down = k_down*2250 + b_down
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(2250, y_kick_up))
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(2250, y_kick_down))
            #kicking the ball
            if (y_kick_up > goal_max_y and y_kick_down > goal_max_y) or (y_kick_up < -goal_max_y and y_kick_down < -goal_max_y):
                actions[idx_at] = KickActions.Straight(aux.Point(2250, 0))
                field.strategy_image.draw_circle(aux.Point(2250, 0))
            else:
                if (goal_max_y - y_kick_up) > (y_kick_down + goal_max_y):
                    actions[idx_at] = KickActions.Straight(aux.Point(2250, goal_max_y))
                    field.strategy_image.draw_circle(aux.Point(2250, goal_max_y))
                else:
                    actions[idx_at] = KickActions.Straight(aux.Point(2250, -goal_max_y))
                    field.strategy_image.draw_circle(aux.Point(2250, -goal_max_y))