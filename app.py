import sqlite3
import json
import os
import datetime
from flask import Flask, render_template, request, jsonify, g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'pantry.db')

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def check_and_migrate_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS categories (id TEXT PRIMARY KEY, name TEXT, color TEXT);
            CREATE TABLE IF NOT EXISTS recipe_tags (id TEXT PRIMARY KEY, name TEXT, color TEXT);
            CREATE TABLE IF NOT EXISTS ingredients (id TEXT PRIMARY KEY, name TEXT, emoji TEXT, unit TEXT, cat_id TEXT);
            CREATE TABLE IF NOT EXISTS inventory (ing_id TEXT PRIMARY KEY, qty INTEGER);
            CREATE TABLE IF NOT EXISTS recipes (id TEXT PRIMARY KEY, name TEXT, desc TEXT);
            CREATE TABLE IF NOT EXISTS recipe_tag_link (recipe_id TEXT, tag_id TEXT);
            CREATE TABLE IF NOT EXISTS recipe_ings (recipe_id TEXT, ing_id TEXT, req INTEGER);
            CREATE TABLE IF NOT EXISTS memo (id INTEGER PRIMARY KEY, content TEXT, updated_at TEXT);
        ''')
        
        # 检查 min_qty 字段
        try:
            db.execute("SELECT min_qty FROM recipe_ings LIMIT 1")
        except sqlite3.OperationalError:
            try:
                db.execute("ALTER TABLE recipe_ings ADD COLUMN min_qty INTEGER DEFAULT 1")
                db.commit()
            except: pass

        # 初始化留言板 (如果为空)
        cur = db.cursor()
        if cur.execute('SELECT count(*) FROM memo').fetchone()[0] == 0:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cur.execute('INSERT INTO memo VALUES (1, ?, ?)', ("欢迎使用家庭留言板！\n例如：\n- 记得买葱\n- 今晚不回家吃饭", now_str))
            db.commit()

        # 初始化分类 (如果为空)
        if cur.execute('SELECT count(*) FROM categories').fetchone()[0] == 0:
            cats = [('c1', '青菜', '#10b981'), ('c2', '肉蛋', '#ef4444'), ('c3', '调料', '#f59e0b'), ('c4', '饮品', '#3b82f6')]
            cur.executemany('INSERT INTO categories VALUES (?,?,?)', cats)
            rtags = [('rt1', '🔥麻辣', '#ef4444'), ('rt2', '⚡快手', '#10b981')]
            cur.executemany('INSERT INTO recipe_tags VALUES (?,?,?)', rtags)
            db.commit()

@app.route('/')
def index():
    return render_template('index.html')

# --- 常规数据接口 ---
@app.route('/api/data', methods=['GET'])
def get_all_data():
    db = get_db()
    try:
        cats = [dict(row) for row in db.execute('SELECT * FROM categories')]
        rtags = [dict(row) for row in db.execute('SELECT * FROM recipe_tags')]
        
        ings = []
        for row in db.execute('SELECT * FROM ingredients'):
            d = dict(row)
            d['catId'] = d['cat_id']
            ings.append(d)

        inv_rows = db.execute('SELECT * FROM inventory')
        inventory = {row['ing_id']: row['qty'] for row in inv_rows}
        
        recipes = []
        for r_row in db.execute('SELECT * FROM recipes'):
            r = dict(r_row)
            t_rows = db.execute('SELECT tag_id FROM recipe_tag_link WHERE recipe_id = ?', (r['id'],))
            r['tagIds'] = [row['tag_id'] for row in t_rows]
            i_rows = db.execute('SELECT ing_id as id, req, min_qty FROM recipe_ings WHERE recipe_id = ?', (r['id'],))
            r['ingredients'] = []
            for row in i_rows:
                r['ingredients'].append({
                    'id': row['id'], 
                    'req': bool(row['req']),
                    'minQty': row['min_qty'] if row['min_qty'] is not None else 1
                })
            recipes.append(r)
            
        return jsonify({
            'categories': cats, 'recipeTags': rtags, 'ingredients': ings,
            'inventory': inventory, 'recipes': recipes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 留言板接口 ---
@app.route('/api/memo', methods=['GET'])
def get_memo():
    db = get_db()
    row = db.execute('SELECT * FROM memo WHERE id=1').fetchone()
    return jsonify(dict(row))

@app.route('/api/memo', methods=['POST'])
def save_memo():
    content = request.json.get('content', '')
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db = get_db()
    db.execute('UPDATE memo SET content=?, updated_at=? WHERE id=1', (content, now_str))
    db.commit()
    return jsonify({'status': 'ok', 'time': now_str})

# --- 其他写操作 ---
@app.route('/api/inventory/update', methods=['POST'])
def update_inventory():
    data = request.json
    db = get_db()
    db.execute('INSERT OR REPLACE INTO inventory (ing_id, qty) VALUES (?, ?)', (data['id'], data['qty']))
    db.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/recipe/save', methods=['POST'])
def save_recipe():
    r = request.json
    db = get_db()
    db.execute('INSERT OR REPLACE INTO recipes (id, name, desc) VALUES (?, ?, ?)', (r['id'], r['name'], r['desc']))
    db.execute('DELETE FROM recipe_tag_link WHERE recipe_id = ?', (r['id'],))
    if r['tagIds']:
        db.executemany('INSERT INTO recipe_tag_link VALUES (?, ?)', [(r['id'], tid) for tid in r['tagIds']])
    db.execute('DELETE FROM recipe_ings WHERE recipe_id = ?', (r['id'],))
    if r['ingredients']:
        db.executemany('INSERT INTO recipe_ings (recipe_id, ing_id, req, min_qty) VALUES (?, ?, ?, ?)', 
                       [(r['id'], item['id'], 1 if item['req'] else 0, item['minQty']) for item in r['ingredients']])
    db.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/recipe/delete', methods=['POST'])
def delete_recipe():
    rid = request.json['id']
    db = get_db()
    db.execute('DELETE FROM recipes WHERE id = ?', (rid,))
    db.execute('DELETE FROM recipe_tag_link WHERE recipe_id = ?', (rid,))
    db.execute('DELETE FROM recipe_ings WHERE recipe_id = ?', (rid,))
    db.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/meta/save', methods=['POST'])
def save_meta_item():
    data = request.json
    type_ = data['type']
    mode = data.get('mode', 'add')
    id_ = data['id']
    db = get_db()
    
    if type_ == 'ingredient':
        db.execute('INSERT OR REPLACE INTO ingredients (id, name, emoji, unit, cat_id) VALUES (?,?,?,?,?)', 
                   (id_, data['name'], data['emoji'], data['unit'], data['catId']))
        if mode == 'add':
            db.execute('INSERT OR IGNORE INTO inventory (ing_id, qty) VALUES (?, 0)', (id_,))
    elif type_ == 'category':
        db.execute('INSERT OR REPLACE INTO categories (id, name, color) VALUES (?,?,?)', (id_, data['name'], data['color']))
    elif type_ == 'recipeTag':
        db.execute('INSERT OR REPLACE INTO recipe_tags (id, name, color) VALUES (?,?,?)', (id_, data['name'], data['color']))
    db.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/meta/delete', methods=['POST'])
def delete_meta_item():
    data = request.json
    t = data['type']
    id_ = data['id']
    db = get_db()
    if t == 'ingredient':
        db.execute('DELETE FROM ingredients WHERE id = ?', (id_,))
        db.execute('DELETE FROM inventory WHERE ing_id = ?', (id_,))
    elif t == 'category':
        db.execute('DELETE FROM categories WHERE id = ?', (id_,))
    elif t == 'recipeTag':
        db.execute('DELETE FROM recipe_tags WHERE id = ?', (id_,))
        db.execute('DELETE FROM recipe_tag_link WHERE tag_id = ?', (id_,))
    db.commit()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    check_and_migrate_db()
    app.run(host='0.0.0.0', port=5000, debug=True)