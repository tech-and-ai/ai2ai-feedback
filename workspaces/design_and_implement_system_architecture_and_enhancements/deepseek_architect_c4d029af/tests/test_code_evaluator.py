# Test cases for Code Evaluator
import unittest
from src.evaluation.code_evaluator import CodeEvaluator

class TestCodeEvaluator(unittest.TestCase):
    def test_evaluate(self):
        evaluator = CodeEvaluator()
        feedback = 'some feedback'
        agent_id = 1
        evaluator.evaluate(agent_id, feedback)
        self.assertIn(agent_id, evaluator.feedback)