"""
Unit tests for the sumatra.web module
"""

import unittest
import os
from pprint import pprint

import sumatra.web
from django.core.exceptions import ObjectDoesNotExist
from django.core import management
from django.core.urlresolvers import reverse
from sumatra.recordstore.django_store import DjangoRecordStore

from test_recordstore import MockRecord, setup as recordstore_setup, teardown as recordstore_teardown
import sumatra.projects

def setup():
    global store, orig_load_project, Client
    import django.conf
    settings = django.conf.settings
    store = DjangoRecordStore(db_file="test.db")
    settings.ROOT_URLCONF = 'sumatra.web.urls'
    settings.INSTALLED_APPS = list(settings.INSTALLED_APPS) + ['sumatra.web']
    management.setup_environ(settings)
    import django.test.client
    Client = django.test.client.Client
    import django.test.utils
    django.test.utils.setup_test_environment()
    
    recordstore_setup()
    orig_load_project = sumatra.projects.load_project
    sumatra.projects.load_project = lambda: MockProject()

def clean_up():
    if os.path.exists("test.db"):
        os.remove("test.db")    

def teardown():
    recordstore_teardown()
    sumatra.projects.load_project = orig_load_project
    clean_up()


class MockProject(object):
    name = "TestProject"

def add_some_records():
    global store
    r1 = MockRecord("record1")
    r2 = MockRecord("record2")
    r3 = MockRecord("record3")
    for r in r1, r2, r3:
        #print "saving record %s" % r.label
        store.save(MockProject.name, r)

class MockDataStore(object):
    def get_content(self, key, path, max_length=100):
        if path == "non_existent_file.txt":
            raise IOError()
        else:
            return ""


class TestWebInterface(unittest.TestCase):
    
    def test_root(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project_name"],
                         MockProject.name)

    def test__nonexistent_record_should_return_404(self):
        c = Client()
        self.assertRaises(ObjectDoesNotExist,
                          c.get, '/record0/')
 
    def test__record_detail(self):
        add_some_records()
        c = Client()
        response = c.get("/record1/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["record"].label, "record1")

    def test__show_file_csv(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.csv")
        assert 'show_csv.html' in [t.name for t in response.template]
        
    def test__show_file_txt(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.txt")
        assert 'show_file.html' in [t.name for t in response.template]

    def test__show_file_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.png")
        assert 'show_image.html' in [t.name for t in response.template]

    def test__show_file_other(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=test_file.doc")
        assert 'show_file.html' in [t.name for t in response.template]
        assert "Can't display" in response.context["content"] 

    def test__show_nonexistent_file(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/datafile?path=non_existent_file.txt")
        assert 'show_file.html' in [t.name for t in response.template]
        assert "File not found" in response.context["content"] 

    def test__show_image(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/image?path=test_file.jpg")
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test__show_diff(self):
        sumatra.web.views.get_data_store = lambda t,p: MockDataStore()
        c = Client()
        response = c.get("/record1/diff/")
        assert 'show_diff.html' in [t.name for t in response.template]


if __name__ == '__main__':
    setup()
    unittest.main()
    teardown()
