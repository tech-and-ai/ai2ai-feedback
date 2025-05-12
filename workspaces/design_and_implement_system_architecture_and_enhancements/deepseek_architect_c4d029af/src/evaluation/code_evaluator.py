# Code Evaluator will assess and provide feedback on agent code

class CodeEvaluator:
    def __init__(self):
        self.feedback = {}

    def evaluate(self, agent_id, feedback):
        self.feedback[agent_id] = feedback