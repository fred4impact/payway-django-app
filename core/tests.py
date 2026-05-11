from django.test import TestCase


class HealthEndpointsTests(TestCase):
    def test_liveness_returns_up(self):
        r = self.client.get('/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'UP')

    def test_readiness_returns_up_when_db_available(self):
        r = self.client.get('/ready/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['status'], 'UP')
        self.assertEqual(data['checks']['database'], 'UP')

    def test_actuator_health_matches_readiness_when_db_ok(self):
        r = self.client.get('/actuator/health/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['status'], 'UP')
        self.assertEqual(data['components']['db']['status'], 'UP')

    def test_actuator_liveness_alias(self):
        r = self.client.get('/actuator/health/liveness/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['status'], 'UP')

    def test_api_discovery_lists_health_and_json_routes(self):
        r = self.client.get('/api/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('health', data)
        self.assertIn('/health/', data['health']['liveness'])
        self.assertTrue(any('security/summary' in x['path'] for x in data['json_apis']))
