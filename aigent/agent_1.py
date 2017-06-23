#!/usr/bin/env python

# The striker agent
import time
import numpy as np
import random
from soccerpy.agent import Agent as baseAgent
from soccerpy.world_model import WorldModel



class Agent(baseAgent):
    """
    The extended Agent class with specific heuritics
    """

    def think(self):
        """
        Performs a single step of thinking for our agent.  Gets called on every
        iteration of our think loop.
        """

        # DEBUG:  tells us if a thread dies
        if not self.__think_thread.is_alive() or not self.__msg_thread.is_alive():
            raise Exception("A thread died.")

        # take places on the field by uniform number
        if not self.in_kick_off_formation:
            print "the side is", self.wm.side

            # used to flip x coords for other side
            side_mod = 1
            if self.wm.side == WorldModel.SIDE_R:
                side_mod = -1

            if self.wm.uniform_number == 1:
                self.wm.teleport_to_point((-5 * side_mod, 30))
            elif self.wm.uniform_number == 2:
                self.wm.teleport_to_point((-40 * side_mod, 15))
            elif self.wm.uniform_number == 3:
                self.wm.teleport_to_point((-40 * side_mod, 00))
            elif self.wm.uniform_number == 4:
                self.wm.teleport_to_point((-40 * side_mod, -15))
            elif self.wm.uniform_number == 5:
                self.wm.teleport_to_point((-5 * side_mod, -30))
            elif self.wm.uniform_number == 6:
                self.wm.teleport_to_point((-20 * side_mod, 20))
            elif self.wm.uniform_number == 7:
                self.wm.teleport_to_point((-20 * side_mod, 0))
            elif self.wm.uniform_number == 8:
                self.wm.teleport_to_point((-20 * side_mod, -20))
            elif self.wm.uniform_number == 9:
                self.wm.teleport_to_point((-10 * side_mod, 0))
            elif self.wm.uniform_number == 10:
                self.wm.teleport_to_point((-10 * side_mod, 20))
            elif self.wm.uniform_number == 11:
                self.wm.teleport_to_point((-10 * side_mod, -20))

            self.in_kick_off_formation = True

            return
        
        if self.wm.side == WorldModel.SIDE_R:
            self.enemy_goal_pos = (-55, 0)
            self.own_goal_pos = (55, 0)
        else:
            self.enemy_goal_pos = (55, 0)
            self.own_goal_pos = (-55, 0)

        #if not self.wm.is_before_kick_off() or self.wm.is_kick_off_us() or self.wm.is_playon():
            
            # The main decision loop
             #check if it is in training episode or actual evaluation
        if not self.wm.is_before_kick_off():

            self.num_of_episodes = self.wm.get_episodes()
            self.episodes_required = self.wm.get_required_episodes()

            if self.num_of_episodes<= self.episodes_required:
                print "Training for player ",self.wm.uniform_number
                return self.calculate_qvalues()
            else:
                print "Training complete"
                for i in self.weights:
                    print i
                return None

      


    # Heuristics begin

    # check if ball is close to self
    def ball_close(self):
        return self.wm.ball.distance < 10

    # check if enemy goalpost is close enough
    def goalpos_close(self):
        return self.wm.get_distance_to_point(self.enemy_goal_pos) < 20

    # check if path to target's coordinate is clear, by direction
    def is_clear(self, target_coords):
        q = self.wm.get_nearest_enemy()
        if q == None:
            return False
        q_coords = self.wm.get_object_absolute_coords(q)
        qDir = self.wm.get_angle_to_point(q_coords)
        qDist = self.wm.get_distance_to_point(q_coords)
        
        tDir = self.wm.get_angle_to_point(target_coords)
        tDist = self.wm.get_distance_to_point(target_coords)

        # the closest teammate is closer, or angle is clear
        return tDist < qDist or abs(qDir - tDir) > 20


    # Action decisions start
    # 
    # find the ball by rotating if ball not found
    def find_ball(self):
        # find the ball
        #print self.wm.ball.direction, "is the ball direction"
        if self.wm.ball is None or self.wm.ball.direction is None:
            
            self.wm.ah.turn(30)
            print "Ball not in range, turning"
            if  self.wm.ball is not None and not -7 <= self.wm.ball.direction <= 7:
                print "Turning ", self.wm.ball.direction/2
                self.wm.ah.turn(self.wm.ball.direction / 2)

            return

       

    # look around randomly
    def defaultaction(self):
        # print "def"
        # kick off!
        if self.wm.is_before_kick_off():
            # player 9 takes the kick off
            if self.wm.uniform_number == 9:
                if self.wm.is_ball_kickable():
                    # kick with 100% extra effort at enemy goal
                    self.wm.kick_to(self.enemy_goal_pos, 1.0)
                else:
                    # move towards ball
                    if self.wm.ball is not None:
                        if (self.wm.ball.direction is not None and
                                -7 <= self.wm.ball.direction <= 7):
                            self.wm.ah.dash(50)
                        else:
                            self.wm.turn_body_to_point((0, 0))

                # turn to ball if we can see it, else face the enemy goal
                if self.wm.ball is not None:
                    self.wm.turn_neck_to_object(self.wm.ball)

                return

        # attack!
        else:
            # find the ball
            if self.wm.ball is None or self.wm.ball.direction is None:
                self.wm.ah.turn(30)

                return

            # kick it at the enemy goal
            if self.wm.is_ball_kickable():
                self.wm.kick_to(self.enemy_goal_pos, 1.0)
                return
            else:
                # move towards ball
                if -7 <= self.wm.ball.direction <= 7:
                    self.wm.ah.dash(65)
                else:
                    # face ball
                    self.wm.ah.turn(self.wm.ball.direction / 2)

                return



    # condition for shooting to the goal
    def shall_shoot(self):
        # if self.wm.is_ball_kickable() and self.goalpos_close() and self.is_clear(self.enemy_goal_pos):
        #     return 1:
        # return 0
        return self.wm.is_ball_kickable() and self.goalpos_close() and self.is_clear(self.enemy_goal_pos)

    # do shoot
    def shoot(self):
        print "shoot"
        return self.wm.kick_to(self.enemy_goal_pos, 1.0)

    # condition for passing to the closest teammate
    # if can kick ball, teammate is closer to goal, path clear
    def shall_pass(self):
        # self.defaultaction()
        p = self.wm.get_nearest_teammate()
        if p == None:
            return False
        p_coords = self.wm.get_object_absolute_coords(p)
        pDistToGoal = self.wm.euclidean_distance(p_coords, self.enemy_goal_pos)
        myDistToGoal = self.wm.get_distance_to_point(self.enemy_goal_pos)
        # kickable, pass closer to goal, path is clear
        return self.wm.is_ball_kickable() and pDistToGoal < myDistToGoal and self.is_clear(p_coords)

    # do passes
    def passes(self):
        print "pass"
        p = self.wm.get_nearest_teammate()
        if p == None:
            return False
        p_coords = self.wm.get_object_absolute_coords(p)
        dist = self.wm.get_distance_to_point(p_coords)
        power_ratio = 2*dist/55.0
        # kick to closest teammate, power is scaled
        return self.wm.kick_to(p_coords, power_ratio)

    # condition for dribbling, if can't shoot or pass
    def shall_dribble(self):
        # find the ball
        # self.find_ball()
        # if self.wm.ball is None or self.wm.ball.direction is None:
            # self.wm.ah.turn(30)
        return self.wm.is_ball_kickable()

    # dribble: turn body, kick, then run towards ball
    def dribble(self):
        #print "dribbling"
        self.wm.kick_to(self.enemy_goal_pos, 1.0)
        self.wm.turn_body_to_point(self.enemy_goal_pos)
        self.wm.align_neck_with_body()
        self.wm.ah.dash(50)
        return

    # if enemy has the ball, and not too far move towards it
    def shall_move_to_ball(self):
        # while self.wm.ball is None:
            # self.find_ball()
        # self.wm.align_neck_with_body()
        return self.wm.is_ball_owned_by_enemy() and self.wm.ball.distance < 30

    # move to ball, if enemy owns it
    def move_to_ball(self):
        if(self.wm.ball is not None):
            self.wm.turn_body_to_point(self.wm.get_object_absolute_coords(self.wm.ball))
            self.wm.align_neck_with_body()
            #print self.wm.ball.distance, "Distance from ball is"
            self.wm.ah.dash(60)
        else:
            self.find_ball()
        return    
    # defensive, when ball isn't ours, and has entered our side of the field
    def shall_move_to_defend(self):
        # self.defaultaction()
        if self.wm.ball is not None or self.wm.ball.direction is not None:
            b_coords = self.wm.get_object_absolute_coords(self.wm.ball)
            return self.wm.is_ball_owned_by_enemy() and self.wm.euclidean_distance(self.own_goal_pos, b_coords) < 55.0
        return False

    # defend
    def move_to_defend(self):
        print "move_to_defend"
        q = self.wm.get_nearest_enemy()
        if q == None:
            return False
        q_coords = self.wm.get_object_absolute_coords(q)
        qDir = self.wm.get_angle_to_point(q_coords)
        qDistToOurGoal = self.wm.euclidean_distance(self.own_goal_pos, q_coords)
        # if close to the goal, aim at it
        if qDistToOurGoal < 55:
            self.wm.turn_body_to_point(q_coords)
        # otherwise aim at own goalpos, run there to defend
        else:
            self.wm.turn_body_to_point(self.own_goal_pos)

        self.wm.align_neck_with_body()
        self.wm.ah.dash(80)
        return

    # when our team has ball, and self is not close enough to goalpos. advance to enemy goalpos
    def shall_move_to_enemy_goalpos(self):
        return self.wm.is_ball_owned_by_us() and not self.goalpos_close()

    # if our team has the ball n u r striker
    def move_to_enemy_goalpos(self):
        print "move_to_enemy_goalpos"
        if self.wm.is_ball_kickable():
            # kick with 100% extra effort at enemy goal
            self.wm.kick_to(self.enemy_goal_pos, 1.0)
        self.wm.turn_body_to_point(self.enemy_goal_pos)
        self.wm.align_neck_with_body()
        self.wm.ah.dash(70)
        return




###########################################################################################################
###########################################################################################################
    
    def set_flags_prev_state(self):
        if self.wm.is_ball_owned_by_enemy():
            self.wm.prev_ball_with_enemy = 1
        if self.wm.is_ball_owned_by_us():
            self.wm.prev_ball_with_us = 1
       

    def set_flags_next_state(self):
        if self.wm.is_ball_owned_by_enemy():
            self.wm.next_ball_with_enemy = 1
        if self.wm.is_ball_owned_by_us():
            self.wm.next_ball_with_us = 1




    def get_action(self):
        
        a = random.randrange(0,3)
        return a
        #print "Random Number generated ",a    


    def get_features(self):
        a =  self.wm.get_nearest_team_dist()
        b =  self.wm.enemies_in_range()
        c =  self.wm.distance_to_goal()
        d =  self.wm.should_shoot()
        e =  self.wm.is_ball_owned_by_us()
        f =  self.wm.is_ball_owned_by_enemy()
        g =  self.wm.play_mode
        #h =  self.wm.ball.distance
        features = (a,b,c,d,e,f,g)
        #features = (1, 2, 3)
        print type(features)  
        return features


    ##  More things to be added to this function    
    def get_reward(self):

        if self.wm.prev_ball_with_us and self.wm.next_ball_with_us:
            return 5
        if self.wm.prev_ball_with_us and self.wm.next_ball_with_enemy:
            return -10
        if self.wm.prev_ball_with_us and not self.wm.next_ball_with_enemy and not self.wm.next_ball_with_us:
            return -5
        if self.wm.prev_ball_with_enemy and self.wm.next_ball_with_enemy:
            return -5
        if self.wm.prev_ball_with_enemy and self.wm.next_ball_with_us:
            return 10
        if self.wm.prev_ball_with_enemy and not self.wm.next_ball_with_us and not self.wm.next_ball_with_enemy:
            return 5
        else:
            return 0
        if self.wm.side == WorldModel.SIDE_L:
            fouls = [WorldModel.PlayModes.KICK_IN_R,WorldModel.PlayModes.FREE_KICK_R,WorldModel.PlayModes.CORNER_KICK_R,WorldModel.PlayModes.OFFSIDE_L]
            
        else:
            fouls = [WorldModel.PlayModes.KICK_IN_L,WorldModel.PlayModes.FREE_KICK_L,WorldModel.PlayModes.CORNER_KICK_L,WorldModel.PlayModes.OFFSIDE_R]    
        if self.wm.is_ball_owned_by_us():
            return 10
        elif self.wm.is_ball_owned_by_enemy():
            return -20
        elif self.wm.play_mode in fouls:
            return -100    
        elif self.side == WorldModel.SIDE_L and self.wm.last_message == WorldModel.RefereeMessages.GOAL_R:
            return -200
        elif self.side == WorldModel.SIDE_R and self.wm.last_message == WorldModel.RefereeMessages.GOAL_L:
            return 200
        
                    

        else:
            return 5    
    
    #weights ad qvalues icreasing expoentiatlly.Features should return small values

    def calculate_qvalues(self):
        features = self.get_features()
        print "before old_q features",features
        weights  = self.wm.weight
        features = list(features)
        #print "weights ", weights
        print type(features)

        #old_q = self.wm.old_q
        new_q = 0
        for w,f in zip(weights,features):
            
            print "Weight is ",w
            print "Feature is ",f
            new_q = new_q + w*f
        print self.wm.old_q,new_q
        reward = self.get_reward()
        print "reward ", reward
        self.set_flags_prev_state()
        action_chosen = self.get_action()
        self.perform_action(action_chosen)  
        self.set_flags_next_state()
        
        # time.sleep(0.5)
        # self.perform_action(action_chosen)
        # features = self.get_features()
        # print "after old_q features",features
        # for w,f in zip(weights,features):
        #     #print "Calculatomg new"
        #     #print "new weight ",w
        #     #print "new feature",f
        #     new_q = new_q + w*f
        # print "old_q ",old_q," new_q ", new_q

        diff = (reward + (self.wm.gamma*new_q)) - self.wm.old_q
        count = 0
        for w,f in zip(weights,features):
             w = w + (self.wm.learning_rate*diff*f)
             ##print "New w is ",w
             self.wm.weight[count] = w
             count = count + 1
        b=sum(weights)
        count = 0
        print "weights sum  ", b
        for w in weights:
            w=w/b
            self.wm.weight[count] = w
            count = count + 1

        self.wm.old_q = new_q
        if self.wm.is_terminal():
            print "terminal state"
            self.num_of_episodes = self.num_of_episodes + 1



    
    def perform_action(self,action_chosen):
        print "Action ",action_chosen
        if action_chosen == 0:
            if self.shall_shoot():
                return self.shoot()
            else:
                return self.perform_action(random.randrange(0,3))   
        elif action_chosen == 1:
            if self.shall_pass():
                return self.passes()
            else:
                return self.perform_action(random.randrange(0,3))

        elif action_chosen == 2:
            print "move to ball"
            return self.move_to_ball()


        else:
            return self.dribble()


    def decisionLoop(self):
        try:
            self.find_ball()
            # if should shoot, full power
            if self.shall_shoot():
                return self.shoot()
            # else shd pass to closest teammate
            elif self.shall_pass():
                return self.passes()
            # else shd dribble
            elif self.shall_dribble():
                return self.dribble()
            elif self.shall_move_to_ball():
                return self.move_to_ball()
            elif self.shall_move_to_defend():
                return self.move_to_defend()
            elif self.shall_move_to_enemy_goalpos():
                return self.move_to_enemy_goalpos()
            else:
                return self.defaultaction()
        except:
            # print "exceptions thrown, using fallback"
            self.defaultaction()
        


# by role: striker, defender
# do the same preconds, but def on role diff actions
# 1. 
# shoot:
# close enuf to ball and to self.enemy_goal_pos
# if self.wm.ball.distance < 10 and self.get_distance_to_point(self.enemy_goal_pos) < 20 and self.is_ball_kickable():



# shoot
# pass
# move

# striker:
# 

# strategy: ordered
# 1. close to ball: grab, carry toward goal, pass or shoot
# 2. ain't, move to enemy (if enemy has ball), goal (if we have ball n jersey num), ball (if enemy n closest, or jersey num)
# 3. 

# conditions shd be:
# shoot: ball aint none, ball kickable, close to goalpos


# Enum fields
# self.get_distance_to_point(self.enemy_goal_pos)
# self.get_angle_to_point(self.enemy_goal_pos)
# self.wm.ball.distance
# self.wm.ball.direction
# p = self.get_nearest_teammate()
# p.distance
# p.direction
# q = self.get_neatest_enemy()
# q.distance
# q.direction
# self.is_ball_owned_by_us
# self.is_ball_owned_by_enemy
# self.is_ball_kickable

# actions and their triggers
# shoot
# pass
# move

# print dir(WorldModel(''))
# print dir(Agent())

# va = 1
# print None or va[0]
# print random.randrange(-30,30)