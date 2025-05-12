# Test cases for AI Explainer
import unittest
from src.explanation.ai_explainer import AiExplainer

class TestAiExplainer(unittest.TestCase):
    def test_add_and_get_explanation(self):
        explainer = AiExplainer()
        explanation = 'some explanation'
        agent_id = 1
        explainer.add_explanation(agent_id, explanation)
        self.assertIn(agent_id, explainer.explanations)