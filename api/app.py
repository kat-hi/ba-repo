from flask import Flask, jsonify, g
from flask import abort
from flask_cors import CORS

from api.db import query_db

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/branches", methods=['GET'])
def get_branches():
    branches = query_db('select * from Branches')
    return jsonify(branches)


@app.route("/revisions", methods=['GET'])
def get_revision():
    revisions = query_db('select * from Revisions')
    return jsonify(revisions)


@app.route("/branches/<branch_id>", methods=['GET'])
def get_branches_by_id(branch_id):
    branch = query_db(f'select * from Branches where Branches.id == ?', (branch_id,))
    if not branch:
        abort(404)
    return jsonify(branch)


@app.route("/branches/<branch_id>/revisions", methods=['GET'])
def get_branches_revisions(branch_id):
    print("/branches/<branch_id>/revisions")
    revisions = query_db(
        'select Revisions.hash, Branches.name from Revisions '
        'INNER JOIN Branches ON Revisions.affected_branch = Branches.id '
        'WHERE Revisions.affected_branch == ?', (branch_id,))
    if not revisions:
        abort(404)
    for r in revisions:
        print(r)
    return jsonify(revisions)


@app.route("/revisions/effects-total/<revision_hash>", methods=['GET'])
def get_effect_by_commit(revision_hash):
    effects = query_db(
        'select * from Revision_ChangedFile_Effect '
        'INNER JOIN Revisions ON Revisions.hash = Revision_ChangedFile_Effect.revision_hash '
        'WHERE Revisions.hash == ?', (revision_hash,))
    if not effects:
        print(f"{revision_hash} not found")
        data = {"LOC_delta": 99, "Comments_delta": 99}
    else:
        total_loc = 0
        total_comments = 0
        for effect in effects:
            total_loc += effect["LOC_delta"]
            total_comments += effect["Comments_delta"]
        data = {"LOC_delta": total_loc, "Comments_delta": total_comments}
    return jsonify(data)


@app.route("/revisions/merges/<revisions_id>/transported_revisions", methods=['GET'])
def get_transported_revisions(revisions_id):
    print("get transported revisions")
    revisions = query_db(
        'select Revisions.hash from Revisions '
        'WHERE Revisions.related_merge_commit == ?', (revisions_id,))
    if not revisions:
        abort(404)

    return jsonify(revisions)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
