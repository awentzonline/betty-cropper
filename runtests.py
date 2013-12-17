#!/usr/bin/env python

import os
if 'SETTINGS_MODULE' not in os.environ:
    os.environ['SETTINGS_MODULE'] = "testsettings"

import unittest
import tempfile
import shutil
import json

from betty import app
from betty.models import Image
from betty.database import db_session, init_db

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'test_data')

class BettyTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        image_root = tempfile.mkdtemp()
        app.config.update({
            'IMAGE_ROOT': image_root,
        })
        self.client = app.test_client()  
        init_db()

    def test_image_upload(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            headers = [('X-Betty-Api-Key', 'noop')]
            res = self.client.post('/api/new', headers=headers, data=dict(
                image=(lenna, 'Lenna.png'),
            ))

        assert res.status_code == 200
        response_json = json.loads(res.data)
        assert response_json.get('name') == 'Lenna.png'
        assert response_json.get('width') == 512
        assert response_json.get('height') == 512

        image = Image.query.get(response_json['id'])
        assert os.path.exists(image.path())
        assert os.path.exists(image.src_path())

        # Now let's test that a crop will return properly.
        res = self.client.get('/%s/1x1/256.jpg' % image.id)
        assert res.headers['Content-Type'] == 'image/jpeg'
        assert res.status_code == 200
        assert os.path.exists(os.path.join(image.path(), '1x1', '256.jpg'))

    def test_image_selection_update_api(self):
        image = Image(name="Testing", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        new_selection = {
            'x0': 1,
            'y0': 1,
            'x1': 510,
            'y1': 510
        }
        headers = [('Content-Type', 'application/json'), ('X-Betty-Api-Key', 'noop')]

        res = self.client.post('/api/%s/1x1' % image.id, headers=headers, data=json.dumps(new_selection))
        assert res.status_code == 200

        db_session.refresh(image, ['selections'])
        assert new_selection == image.selections['1x1']

        bad_selection = {
            'x0': 1,
            'x1': 510
        }
        res = self.client.post('/api/%s/1x1' % image.id, headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 400

        res = self.client.post('/api/%s/original' % image.id, headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 400

        res = self.client.post('/api/10000/1x1', headers=headers, data=json.dumps(bad_selection))
        assert res.status_code == 404

    def test_image_detail(self):
        image = Image(name="Testing", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        headers = [('X-Betty-Api-Key', 'noop')]
        res = self.client.get('/api/%s' % image.id, headers=headers)
        assert res.status_code == 200

        headers = [('Content-Type', 'application/json'), ('X-Betty-Api-Key', 'noop')]
        res = self.client.patch('/api/%s' % image.id, headers=headers, data=json.dumps({'name': 'Updated'}))
        assert res.status_code == 200
        db_session.refresh(image)
        assert image.name == 'Updated'

    def test_bad_image_data(self):
        lenna_path = os.path.join(TEST_DATA_PATH, 'Lenna.png')
        with open(lenna_path, 'r') as lenna:
            headers = [('X-Betty-Api-Key', 'noop')]
            res = self.client.post('/api/new', headers=headers, data=dict(
                image=(lenna, 'Lenna.png'),
            ))

        assert res.status_code == 200
        response_json = json.loads(res.data)
        assert response_json.get('name') == 'Lenna.png'
        assert response_json.get('width') == 512
        assert response_json.get('height') == 512

        # Now that the image is uploaded, let's fuck up the data.
        image = Image.query.get(response_json['id'])
        image.width = 1024
        image.height = 1024
        db_session.add(image)
        db_session.commit()

        id_string = ""
        for index,char in enumerate(str(image.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        res = self.client.get('%s/1x1/400.jpg' % id_string)
        assert res.status_code == 200

    def test_image_search(self):
        image = Image(name="BLERGH", width=512, height=512)
        db_session.add(image)
        db_session.commit()

        headers = [('X-Betty-Api-Key', 'noop')]
        res = self.client.get('/api/search?q=blergh', headers=headers)
        assert res.status_code == 200

    def tearDown(self):
        # os.unlink(app.config['DATABASE'].replace('sqlite:///', ''))
        shutil.rmtree(app.config['IMAGE_ROOT'])


if __name__ == '__main__':
    unittest.main()