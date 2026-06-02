import unittest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aroma_sim import AromaOperationsSimulator

class TestAromaSimulator(unittest.TestCase):
    def setUp(self):
        self.config = {
            'Canteen': {'servers': 4, 'mean_service_min': 3.5},
            'FastFood': {'servers': 3, 'mean_service_min': 5.0}
        }
        self.sim = AromaOperationsSimulator(self.config, simulation_time_hours=2.0, seed=123)

    def test_simulation_runs_and_completes(self):
        rates = {'Canteen': 0.8, 'FastFood': 0.4}
        res = self.sim.run_simulation(rates)
        self.assertIn('Canteen', res)
        self.assertIn('FastFood', res)
        self.assertGreater(res['Canteen']['completed_customers'], 0)
        self.assertGreaterEqual(res['Canteen']['avg_wait_time_min'], 0.0)

    def test_zero_arrivals(self):
        rates = {'Canteen': 0.001, 'FastFood': 0.001}
        res = self.sim.run_simulation(rates)
        self.assertEqual(res['Canteen']['completed_customers'], 0)

if __name__ == '__main__':
    unittest.main()
