'''
Created on Sep 9, 2013

@author: felix
'''

from smach import State, UserData

from common import Condition, Precondition, Effect, VariableEffect, Action

from uashh_smach.manipulator.look_around import get_lookaround_smach
from uashh_smach.manipulator.move_arm import get_move_arm_to_joints_positions_state


#from config_scitos import ARM_POSE_FOLDED, ARM_POSE_FLOOR
# FIXME: remove these duplicate constants!! (cyclic import issue)
ARM_NAMES = ['DH_1_2', 'DH_2_3', 'DH_4_4', 'DH_4_5', 'DH_5_6']

ARM_POSE_FOLDED = [0, 0.52, 0.52, -1.57, 0]
ARM_POSE_FOLDED_NAMED = dict(zip(ARM_NAMES, ARM_POSE_FOLDED))

ARM_POSE_FLOOR = [0, 0.96, 0.96, -2.0, -1.57]
ARM_POSE_FLOOR_NAMED = dict(zip(ARM_NAMES, ARM_POSE_FLOOR))



class RGOAPNodeWrapperState(State):
    """Used (by the runner) to add RGOAP nodes (aka instances of RGOAP actions)
    to a SMACH state machine"""
    def __init__(self, node):
        State.__init__(self, outcomes=['succeeded', 'aborted'])
        self.node = node

    def execute(self, userdata):
#        if not self.node.action.is_valid(current_worldstate): TODO: current worldstate not known
#            print "Action isn't valid to worldstate! Aborting executor"
#            print ' action: %r' % self.node.action
#            print ' worldstate:', self.node.worldstate
#            return 'aborted'
#        print "Action %s valid to worldstate" % self.node.action
        if not self.node.action.check_freeform_context():
            print "Action's freeform context isn't valid! Aborting wrapping state for %s", self.node.action
            return 'aborted'
        next_node = self.node.parent_node()
        self.node.action.run(next_node.worldstate)
        return 'succeeded'


class SMACHStateWrapperAction(Action):
    """A special Action to wrap a SMACH state.

    Subclass this class to make a SMACH state available to RGOAP planning.
    """
    def __init__(self, state, preconditions, effects, **kwargs):
        Action.__init__(self, preconditions, effects, **kwargs)
        self.state = state

    def get_remapping(self):
        """Override this to set a remapping.
        Actually planned for future use"""
        return {}

    def translate_worldstate_to_userdata(self, next_worldstate, userdata):
        """Override to make worldstate data available to the state."""
        pass

    def translate_userdata_to_worldstate(self, userdata, next_worldstate):
        """Override to make the state's output available to the worldstate."""
        pass

    def run(self, next_worldstate):
        userdata = UserData()
        self.translate_worldstate_to_userdata(next_worldstate, userdata)
        self.state.execute(userdata)
        raise NotImplementedError, "write a test and remove this raise" # TODO: write test, remove raise




class LookAroundAction(SMACHStateWrapperAction):

    def __init__(self):
        SMACHStateWrapperAction.__init__(self, get_lookaround_smach(glimpse=True),
                                  [Precondition(Condition.get('arm_can_move'), True)],
                                  [VariableEffect(Condition.get('awareness'))])

    def _generate_variable_preconditions(self, var_effects, worldstate, start_worldstate):
        effect = var_effects.pop()  # this action has one variable effect
        assert effect is self._effects[0]
        # increase awareness by one
        precond_value = worldstate.get_condition_value(effect._condition) - 1
        return [Precondition(effect._condition, precond_value, None)]




class FoldArmAction(SMACHStateWrapperAction):

    def __init__(self):
        SMACHStateWrapperAction.__init__(self, get_move_arm_to_joints_positions_state(ARM_POSE_FOLDED),
                                  [Precondition(Condition.get('arm_can_move'), True),
                                   # TODO: maybe remove necessary anti-effect-preconditions
                                   # the currently available alternative would be to use a
                                   # variable effect that can reach any value
                                   Precondition(Condition.get('robot.arm_folded'), False)],
                                  [Effect(Condition.get('robot.arm_folded'), True)])


class MoveArmFloorAction(SMACHStateWrapperAction):

    def __init__(self):
        SMACHStateWrapperAction.__init__(self, get_move_arm_to_joints_positions_state(ARM_POSE_FLOOR),
                                  [Precondition(Condition.get('arm_can_move'), True),
                                   # TODO: maybe remove necessary anti-effect-preconditions
                                   # the currently available alternative would be to use a
                                   # variable effect that can reach any value
                                   Precondition(Condition.get('robot.arm_pose_floor'), False)],
                                  [Effect(Condition.get('robot.arm_pose_floor'), True)])

