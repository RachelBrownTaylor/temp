from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from app.auth import admin_required
import json
import csv
import io
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    stats = current_app.db.get_aggregated_stats()
    all_ratings = current_app.db.get_all_ratings()

    return render_template('admin.html', stats=stats, ratings=all_ratings)

@admin_bp.route('/export/<format>')
@admin_required
def export_ratings(format):
    """Export ratings as CSV or JSON"""
    all_ratings = current_app.db.get_all_ratings()

    if format == 'csv':
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['example_id', 'category', 'model', 'evaluator_id', 'rating', 'timestamp'])

        # Write data
        for rating in all_ratings:
            writer.writerow([
                rating['example_id'],
                rating['category'],
                rating['model_name'],
                rating['evaluator_username'],
                rating['rating'],
                rating['timestamp']
            ])

        # Create response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ratings_export_{timestamp}.csv'

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),  # UTF-8 BOM for Excel
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    elif format == 'json':
        # Create JSON
        export_data = []
        for rating in all_ratings:
            export_data.append({
                'example_id': rating['example_id'],
                'category': rating['category'],
                'model': rating['model_name'],
                'evaluator_id': rating['evaluator_username'],
                'rating': rating['rating'],
                'timestamp': rating['timestamp']
            })

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ratings_export_{timestamp}.json'

        return send_file(
            io.BytesIO(json.dumps(export_data, ensure_ascii=False, indent=2).encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )

    return jsonify({'success': False, 'message': '지원하지 않는 형식입니다.'}), 400

@admin_bp.route('/load_dataset', methods=['POST'])
@admin_required
def load_dataset():
    """Load a new dataset from JSON file"""
    data = request.get_json()
    dataset_path = data.get('dataset_path')

    if not dataset_path:
        return jsonify({'success': False, 'message': '데이터셋 경로가 필요합니다.'}), 400

    # Check if file exists
    if not os.path.exists(dataset_path):
        return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'}), 404

    try:
        # Load and validate JSON
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        # Validate dataset format
        if not isinstance(dataset, list):
            return jsonify({'success': False, 'message': '데이터셋은 배열 형식이어야 합니다.'}), 400

        for i, item in enumerate(dataset):
            # Check required fields
            required_fields = ['category', 'history', 'example_id', 'responses']
            for field in required_fields:
                if field not in item:
                    return jsonify({
                        'success': False,
                        'message': f'항목 {i}: 필수 필드 "{field}"가 누락되었습니다.'
                    }), 400

            # Validate history
            if not isinstance(item['history'], list):
                return jsonify({
                    'success': False,
                    'message': f'항목 {i}: history는 배열이어야 합니다.'
                }), 400

            for turn in item['history']:
                if 'role' not in turn or 'content' not in turn:
                    return jsonify({
                        'success': False,
                        'message': f'항목 {i}: history의 각 항목은 role과 content를 포함해야 합니다.'
                    }), 400

            # Validate responses
            if not isinstance(item['responses'], list) or len(item['responses']) == 0:
                return jsonify({
                    'success': False,
                    'message': f'항목 {i}: responses는 비어있지 않은 배열이어야 합니다.'
                }), 400

            for response in item['responses']:
                if 'model' not in response or 'output' not in response:
                    return jsonify({
                        'success': False,
                        'message': f'항목 {i}: 각 response는 model과 output을 포함해야 합니다.'
                    }), 400

        # Load into database
        current_app.db.load_dataset(dataset)

        return jsonify({
            'success': True,
            'message': f'{len(dataset)}개의 예제가 성공적으로 로드되었습니다.'
        })

    except json.JSONDecodeError as e:
        return jsonify({'success': False, 'message': f'JSON 파싱 오류: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'오류 발생: {str(e)}'}), 500
