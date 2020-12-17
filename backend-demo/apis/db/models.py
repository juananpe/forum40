from flask_restplus import Resource, Namespace

from db import with_database, Database

ns = Namespace('models', description="models api")


@ns.route('/<int:label_id>')
class Models(Resource):
    @with_database
    def get(self, db: Database, label_id):
        models = db.models.find_all_by_label_id(label_id)
        return [(model | {'timestamp': model['timestamp'].isoformat()}) for model in models], 200
