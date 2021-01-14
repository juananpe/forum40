from http import HTTPStatus

from flask_restplus import Resource, Namespace

from db import with_database, Database

ns = Namespace('models', description="models api")


@ns.route('/<int:label_id>')
class Models(Resource):
    @with_database
    def get(self, db: Database, label_id):
        models = sorted(
            db.models.find_all_by_label_id(label_id),
            key=lambda model: model['timestamp']
        )
        return list(models), HTTPStatus.OK
