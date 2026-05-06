from google.cloud import firestore
db = firestore.Client(project='brasili-ia-news')
# Cancela job afetado
db.collection('avatar_jobs').document('cbde490f').update({
    'status': 'cancelled',
    'message': 'Cancelado devido ao bug de injeção de metadata antigo.'
})
