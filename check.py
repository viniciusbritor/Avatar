import json
from google.cloud import firestore
db = firestore.Client(project='brasili-ia-news')
d = db.collection('avatar_jobs').document('82d63a15').get().to_dict()
print(json.dumps({'job_id': '82d63a15', 'status': d.get('status'), 'video': d.get('video_path')}, indent=2))
