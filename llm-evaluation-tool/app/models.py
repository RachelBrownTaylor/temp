import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    """Database handler for SQLite operations"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('evaluator', 'admin'))
            )
        ''')

        # Examples table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                example_id INTEGER UNIQUE NOT NULL,
                category TEXT NOT NULL,
                history TEXT NOT NULL,
                responses TEXT NOT NULL
            )
        ''')

        # Ratings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                example_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (example_id) REFERENCES examples(example_id),
                UNIQUE(user_id, example_id, model_name)
            )
        ''')

        conn.commit()
        conn.close()

    def create_user(self, username, password, role='evaluator'):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)

        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                (username, password_hash, role)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            return dict(user)
        return None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def load_dataset(self, dataset):
        """Load dataset into database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Clear existing examples
        cursor.execute('DELETE FROM examples')

        for item in dataset:
            cursor.execute(
                'INSERT INTO examples (example_id, category, history, responses) VALUES (?, ?, ?, ?)',
                (
                    item['example_id'],
                    item['category'],
                    json.dumps(item['history'], ensure_ascii=False),
                    json.dumps(item['responses'], ensure_ascii=False)
                )
            )

        conn.commit()
        conn.close()

    def get_categories(self):
        """Get all unique categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM examples ORDER BY category')
        categories = [row['category'] for row in cursor.fetchall()]
        conn.close()
        return categories

    def get_examples_by_category(self, category):
        """Get all examples for a specific category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM examples WHERE category = ? ORDER BY example_id',
            (category,)
        )
        examples = []
        for row in cursor.fetchall():
            example = dict(row)
            example['history'] = json.loads(example['history'])
            example['responses'] = json.loads(example['responses'])
            examples.append(example)
        conn.close()
        return examples

    def get_example_by_id(self, example_id):
        """Get a specific example by example_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM examples WHERE example_id = ?', (example_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            example = dict(row)
            example['history'] = json.loads(example['history'])
            example['responses'] = json.loads(example['responses'])
            return example
        return None

    def save_rating(self, user_id, example_id, model_name, rating):
        """Save or update a rating"""
        conn = self.get_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(
            '''INSERT OR REPLACE INTO ratings
               (user_id, example_id, model_name, rating, timestamp)
               VALUES (?, ?, ?, ?, ?)''',
            (user_id, example_id, model_name, rating, timestamp)
        )

        conn.commit()
        conn.close()

    def get_user_ratings(self, user_id, category=None):
        """Get all ratings for a user, optionally filtered by category"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT r.*, e.category
                FROM ratings r
                JOIN examples e ON r.example_id = e.example_id
                WHERE r.user_id = ? AND e.category = ?
            ''', (user_id, category))
        else:
            cursor.execute('''
                SELECT r.*, e.category
                FROM ratings r
                JOIN examples e ON r.example_id = e.example_id
                WHERE r.user_id = ?
            ''', (user_id,))

        ratings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ratings

    def get_user_progress(self, user_id, category):
        """Get evaluation progress for a user in a specific category"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all examples in category
        cursor.execute(
            'SELECT example_id FROM examples WHERE category = ? ORDER BY example_id',
            (category,)
        )
        examples = [row['example_id'] for row in cursor.fetchall()]

        # Get ratings for this user and category
        cursor.execute('''
            SELECT r.example_id, r.model_name, r.rating
            FROM ratings r
            JOIN examples e ON r.example_id = e.example_id
            WHERE r.user_id = ? AND e.category = ?
        ''', (user_id, category))

        ratings = {}
        for row in cursor.fetchall():
            ex_id = row['example_id']
            if ex_id not in ratings:
                ratings[ex_id] = {}
            ratings[ex_id][row['model_name']] = row['rating']

        conn.close()

        progress = []
        for ex_id in examples:
            progress.append({
                'example_id': ex_id,
                'ratings': ratings.get(ex_id, {})
            })

        return progress

    def get_all_ratings(self):
        """Get all ratings (for admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, e.category, u.username as evaluator_username
            FROM ratings r
            JOIN examples e ON r.example_id = e.example_id
            JOIN users u ON r.user_id = u.id
            ORDER BY r.timestamp DESC
        ''')
        ratings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ratings

    def get_aggregated_stats(self):
        """Get aggregated statistics (for admin)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Average by model
        cursor.execute('''
            SELECT model_name, AVG(rating) as avg_rating, COUNT(*) as count
            FROM ratings
            GROUP BY model_name
        ''')
        by_model = [dict(row) for row in cursor.fetchall()]

        # Average by category
        cursor.execute('''
            SELECT e.category, AVG(r.rating) as avg_rating, COUNT(*) as count
            FROM ratings r
            JOIN examples e ON r.example_id = e.example_id
            GROUP BY e.category
        ''')
        by_category = [dict(row) for row in cursor.fetchall()]

        # Average by model and category
        cursor.execute('''
            SELECT e.category, r.model_name, AVG(r.rating) as avg_rating, COUNT(*) as count
            FROM ratings r
            JOIN examples e ON r.example_id = e.example_id
            GROUP BY e.category, r.model_name
        ''')
        by_model_category = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'by_model': by_model,
            'by_category': by_category,
            'by_model_category': by_model_category
        }
