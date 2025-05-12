# API endpoints for managing agent performance data
def register_routes():
    from flask import request, jsonify
    # Example endpoint to add new performance metrics
    @app.route('/add_performance', methods=['POST'])
    def add_performance():
        data = request.get_json()
        new_performance = AgentPerformance(**data)
        db.session.add(new_performance)
        db.session.commit()
        return jsonify({'message': 'Performance data added'}), 201
