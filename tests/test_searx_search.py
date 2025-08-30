import unittest
from unittest.mock import patch, Mock
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sources.tools.searxSearch import searxSearch
from dotenv import load_dotenv
import requests

load_dotenv()

class TestSearxSearch(unittest.TestCase):

    def setUp(self):
        os.environ['SEARXNG_BASE_URL'] = "http://127.0.0.1:8080"
        self.base_url = os.getenv("SEARXNG_BASE_URL")
        self.search_tool = searxSearch(base_url=self.base_url)
        self.valid_query = "test query"
        self.invalid_query = ""

    def test_initialization_with_env_variable(self):
        os.environ['SEARXNG_BASE_URL'] = "http://test.example.com"
        search_tool = searxSearch()
        self.assertEqual(search_tool.base_url, "http://test.example.com")
        del os.environ['SEARXNG_BASE_URL']

    def test_initialization_no_base_url(self):
        if 'SEARXNG_BASE_URL' in os.environ:
            del os.environ['SEARXNG_BASE_URL']
        with self.assertRaises(ValueError):
            searxSearch(base_url=None)
        os.environ['SEARXNG_BASE_URL'] = "http://127.0.0.1:8080"

    @patch('requests.post')
    def test_execute_valid_query(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <article class="result">
            <a class="url_header" href="http://example.com"></a>
            <h3>Example Title</h3>
            <p class="content">Example description.</p>
        </article>
        """
        mock_post.return_value = mock_response
        result = self.search_tool.execute([self.valid_query])
        self.assertIn("Title:Example Title", result)
        self.assertIn("Snippet:Example description.", result)
        self.assertIn("Link:http://example.com", result)

    def test_execute_empty_query(self):
        result = self.search_tool.execute([""])
        self.assertEqual(result, "Error: Empty search query provided.")

    def test_execute_no_query(self):
        result = self.search_tool.execute([])
        self.assertEqual(result, "Error: No search query provided.")

    @patch('requests.post')
    def test_execute_request_exception(self, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Test error")
        with self.assertRaises(Exception) as context:
            self.search_tool.execute([self.valid_query])
        self.assertTrue('Searxng search failed' in str(context.exception))

    @patch('requests.post')
    def test_execute_no_results(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "No results found"
        mock_post.return_value = mock_response
        result = self.search_tool.execute(["query with no results"])
        self.assertEqual(result, "No search results, web search failed.")

    def test_execution_failure_check_error(self):
        output = "Error: Something went wrong"
        self.assertTrue(self.search_tool.execution_failure_check(output))

    def test_execution_failure_check_no_error(self):
        output = "Search completed successfully"
        self.assertFalse(self.search_tool.execution_failure_check(output))

if __name__ == '__main__':
    unittest.main()
