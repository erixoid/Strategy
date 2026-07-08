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
        self.que = 1
        self.active_robots: list[int] = []
        self.active_enemies: list[int] = []
        self.pas = False

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
                return [Actions.Stop()] * const.TEAM_ROBOTS_MAX_COUNT
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
        ball = field.ball.get_pos()
        for i in range(16):
            if field.allies[i].is_used():
                self.active_robots.append(i)

        for i in range(16):
            if field.enemies[i].is_used():
                self.active_enemies.append(i)

        if len(self.active_enemies) > 0:
            gk_en = self.active_enemies[0]
        if len(self.active_robots) > 2:
            at1_id = self.active_robots[1]
            at2_id = self.active_robots[2]
            gk_id = self.active_robots[0]
            if len(self.active_enemies) > 0:
                self.attacker(field, actions, gk_en, at1_id, at2_id)
                self.attacker2(field, actions, at1_id, at2_id, gk_en)
            self.goalkeeper(field=field,actions=actions, idx_gk=gk_id, idx_at=at1_id, idx_at2=at2_id)
            
            #Attacker
        self.prev_ball = ball
        
    def goalkeeper(self, field: fld.Field, actions: list[Optional[Action]], idx_gk: int, idx_at: int, idx_at2: int):
        ball = field.ball.get_pos()
        if aux.is_point_inside_poly(ball, field.ally_goal.hull):
            if self.que == 1:
                actions[idx_gk] = KickActions.Straight(field.allies[idx_at].get_pos())
            else:
                actions[idx_gk] = KickActions.Straight(field.allies[idx_at2].get_pos())
            kick = True
        else:
            kick = False

        if ball.x - self.prev_ball.x != 0:
            if field.ball.get_vel().mag() > 10.0 and kick != True:
                k = (ball.y - self.prev_ball.y) / (ball.x - self.prev_ball.x)

                if field.ally_color == const.Color.BLUE:

                    y = self.prev_ball.y - k * self.prev_ball.x + k * (field.ally_goal.center.x + 110)
                    if y >= -400 and y <= 400:
                        # field.strategy_image.draw_circle(aux.Point(field.ally_goal.center.x + 100, y), size_in_mms = 100)  
                        ang = (field.ball.get_pos() - field.allies[idx_gk].get_pos()).arg()
                        actions[idx_gk] = Actions.GoToPoint(aux.Point(field.ally_goal.center.x + 110, y), ang)  
                else: 
                    ang = (field.ball.get_pos() - field.allies[idx_gk].get_pos()).arg()
                    y = self.prev_ball.y - k * self.prev_ball.x + k * (field.ally_goal.center.x + 110)
                    if y <= 400 and y >= -400:
                        actions[idx_gk] = Actions.GoToPoint(aux.Point(field.ally_goal.center.x - 110, y), ang)
        
    def attacker(self, field: fld.Field, actions: list[Optional[Action]], idx_gk: int, idx_at: int, idx_at2: int):
        goal_max_y = 320
        if field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x != 0:
            k_up = (field.allies[idx_at].get_pos().y - field.enemies[idx_gk].get_pos().y - 100) / (field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x)
            b_up = field.allies[idx_at].get_pos().y - k_up * field.allies[idx_at].get_pos().x
            k_down = (field.allies[idx_at].get_pos().y - field.enemies[idx_gk].get_pos().y + 100) / (field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x)
            b_down = field.allies[idx_at].get_pos().y - k_down * field.allies[idx_at].get_pos().x
            y_kick_up = k_up * field.enemy_goal.center.x + b_up
            y_kick_down = k_down*field.enemy_goal.center.x + b_down
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(field.enemy_goal.center.x, y_kick_up))
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(field.enemy_goal.center.x, y_kick_down))
            #kicking the ball
            if self.que == 1:
                if len(self.active_enemies) > 2:
                    dist1 = (field.enemies[self.active_enemies[1]].get_pos() - field.allies[idx_at].get_pos()).mag()
                    dist2 = (field.enemies[self.active_enemies[2]].get_pos() - field.allies[idx_at].get_pos()).mag()

                    if (dist1 < 260) or (dist2 < 260):
                        actions[idx_at] = KickActions.Straight(field.allies[idx_at2].get_pos())
                        self.pas = True
                        if self.is_kicked(field, actions, idx_at):
                            self.que = 2
                            self.pas = False
                    else:
                        self.pas = False

                if ((y_kick_up > goal_max_y and y_kick_down > goal_max_y) or (y_kick_up < -goal_max_y and y_kick_down < -goal_max_y)):
                    if self.pas == False:
                        actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, 0))
                        field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, 0))
                else:
                    if self.pas == False:
                        if (goal_max_y - y_kick_up) > (y_kick_down + goal_max_y):
                            actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, goal_max_y))
                            field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, goal_max_y))
                        else:
                            actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, -goal_max_y))
                            field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, -goal_max_y))
            else:
                ang = (field.ball.get_pos() - field.allies[idx_at].get_pos()).arg()
                if field.allies[idx_at2].get_pos().y >= 0:
                    if field.ally_color == const.Color.BLUE:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(1300, -600), ang)
                    else:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(-1300, -600), ang)
                else:
                    if field.ally_color == const.Color.BLUE:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(1300, 600), ang)
                    else:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(-1300, 600), ang)


    def attacker2(self, field: fld.Field, actions: list[Optional[Action]], idx_at1: int, idx_at: int, idx_gk: int):
        goal_max_y = 320
        if field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x != 0:
            k_up = (field.allies[idx_at].get_pos().y - field.enemies[idx_gk].get_pos().y - 100) / (field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x)
            b_up = field.allies[idx_at].get_pos().y - k_up * field.allies[idx_at].get_pos().x
            k_down = (field.allies[idx_at].get_pos().y - field.enemies[idx_gk].get_pos().y + 100) / (field.allies[idx_at].get_pos().x - field.enemies[idx_gk].get_pos().x)
            b_down = field.allies[idx_at].get_pos().y - k_down * field.allies[idx_at].get_pos().x
            y_kick_up = k_up * field.enemy_goal.center.x + b_up
            y_kick_down = k_down*field.enemy_goal.center.x + b_down
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(field.enemy_goal.center.x, y_kick_up))
            field.strategy_image.draw_line(field.allies[idx_at].get_pos(), aux.Point(field.enemy_goal.center.x, y_kick_down))
            #kicking the ball
            if self.que==2:
                if len(self.active_enemies) > 2:
                    dist1 = (field.enemies[self.active_enemies[1]].get_pos() - field.allies[idx_at].get_pos()).mag()
                    dist2 = (field.enemies[self.active_enemies[2]].get_pos() - field.allies[idx_at].get_pos()).mag()
                    if (dist1 < 260) or (dist2 < 260):
                        actions[idx_at] = KickActions.Straight(field.allies[idx_at1].get_pos())
                        self.pas = True
                        if self.is_kicked(field, actions, idx_at):
                            self.que = 1
                            self.pas = False
                        else:
                            self.pas = False

                if ((y_kick_up > goal_max_y and y_kick_down > goal_max_y) or (y_kick_up < -goal_max_y and y_kick_down < -goal_max_y)):
                    if self.pas == False:
                        actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, 0))
                        field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, 0))
                else:
                    if self.pas == False:
                        if (goal_max_y - y_kick_up) > (y_kick_down + goal_max_y):
                            actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, goal_max_y))
                            field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, goal_max_y))
                        else:
                            actions[idx_at] = KickActions.Straight(aux.Point(field.enemy_goal.center.x, -goal_max_y))
                            field.strategy_image.draw_circle(aux.Point(field.enemy_goal.center.x, -goal_max_y))
            else:
                ang = (field.ball.get_pos() - field.allies[idx_at].get_pos()).arg()
                if field.allies[idx_at1].get_pos().y >= 0:
                    if field.ally_color == const.Color.BLUE:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(1300, -600), ang)
                    else:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(-1300, -600), ang)
                else:
                    if field.ally_color == const.Color.BLUE:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(1300, 600), ang)
                    else:
                        actions[idx_at] = Actions.GoToPoint(aux.Point(-1300, 600), ang)
    def is_kicked(self, field: fld.Field, actions: list[Optional[Action]], idx: int):
        ball = field.ball.get_pos()
        if field.ball.get_vel().mag() > 20:
            if field.is_ball_in(field.allies[idx]) != True:
                ang = (ball - self.prev_ball).arg()
                if abs(ang - field.allies[idx].get_angle()) < 2:
                    return True
        return False
        