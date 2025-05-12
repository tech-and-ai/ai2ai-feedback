# AI Explainer will enable agents to explain their decision making

class AiExplainer:
    def __init__(self):
        self.explanations = {}

    def add_explanation(self, agent_id, explanation):
        self.explanations[agent_id] = explanation