import sqlite3
import hashlib
import os

db_file = os.path.join(os.path.dirname(__file__), 'locker.db')
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print("--- KHỞI TẠO CƠ SỞ DỮ LIỆU GLMS PHOENIX GOLF (SQLITE) ---")

cursor.execute("""
CREATE TABLE IF NOT EXISTS locker_zones (
    zone_id TEXT PRIMARY KEY,
    zone_name TEXT NOT NULL,
    gender TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS locker_tiers (
    tier_id TEXT PRIMARY KEY,
    tier_name TEXT NOT NULL,
    badge_label TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS locker_statuses (
    status_id TEXT PRIMARY KEY,
    status_name TEXT NOT NULL,
    color_code TEXT NOT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS lockers (
    locker_id TEXT PRIMARY KEY,
    locker_number TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    tier_id TEXT NOT NULL,
    current_status TEXT NOT NULL DEFAULT 'INSPECTED',
    qr_token TEXT UNIQUE NOT NULL,
    assigned_guest_name TEXT,
    assigned_at DATETIME,
    last_status_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated_by TEXT DEFAULT 'SYSTEM',
    notes TEXT,
    version INTEGER DEFAULT 1
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS locker_history_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locker_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    action_type TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    user_role TEXT DEFAULT 'STAFF',
    ip_address TEXT,
    user_agent TEXT,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS lost_and_found_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locker_id TEXT NOT NULL,
    item_description TEXT NOT NULL,
    image_data TEXT,
    found_by TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    returned_at DATETIME,
    returned_by TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS long_term_holds (
    hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locker_id TEXT UNIQUE NOT NULL,
    member_name TEXT NOT NULL,
    member_card_no TEXT,
    phone_number TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

# Seed Zones
cursor.executemany("INSERT OR REPLACE INTO locker_zones VALUES (?, ?, ?)", [
    ('MEN', 'Khu Vực Nam', 'MEN'),
    ('WOMEN', 'Khu Vực Nữ', 'WOMEN')
])

# Seed Tiers
cursor.executemany("INSERT OR REPLACE INTO locker_tiers VALUES (?, ?, ?)", [
    ('VIP', 'Hạng VIP', '★ VIP'),
    ('MEMBER_GUEST', 'Hạng Member & Guest', 'M&G')
])

# Seed Statuses
cursor.executemany("INSERT OR REPLACE INTO locker_statuses VALUES (?, ?, ?)", [
    ('INSPECTED', 'Sẵn sàng (Đã dọn)', '#198754'),
    ('IN_USE', 'Đang sử dụng', '#DC3545'),
    ('DIRTY', 'Chờ dọn (Dirty)', '#FFC107'),
    ('RESERVED', 'Member giữ tủ', '#6F42C1'),
    ('OOO', 'Bảo trì / Hỏng', '#6C757D')
])

# Check count
cursor.execute("SELECT COUNT(*) FROM lockers")
count = cursor.fetchone()[0]

if count == 0:
    print("Đang nạp dữ liệu 603 tủ theo đúng sơ đồ Phoenix Golf Resort...")
    lockers_data = []

    # 1. Men VIP: 221 lockers (001 -> 221)
    for i in range(1, 222):
        num = f"{i:03d}"
        l_id = f"M-VIP-{num}"
        qr = f"PHX-{l_id}-" + hashlib.md5(f"M_VIP_{num}_2026".encode()).hexdigest()[:8].upper()
        lockers_data.append((l_id, num, 'MEN', 'VIP', 'INSPECTED', qr, 'SYSTEM'))

    # 2. Men Member & Guest: 276 lockers (222 -> 497)
    for i in range(222, 498):
        num = f"{i:03d}"
        l_id = f"M-MEM-{num}"
        qr = f"PHX-{l_id}-" + hashlib.md5(f"M_MEM_{num}_2026".encode()).hexdigest()[:8].upper()
        lockers_data.append((l_id, num, 'MEN', 'MEMBER_GUEST', 'INSPECTED', qr, 'SYSTEM'))

    # 3. Women VIP: 23 lockers (001 -> 023)
    for i in range(1, 24):
        num = f"{i:03d}"
        l_id = f"W-VIP-{num}"
        qr = f"PHX-{l_id}-" + hashlib.md5(f"W_VIP_{num}_2026".encode()).hexdigest()[:8].upper()
        lockers_data.append((l_id, num, 'WOMEN', 'VIP', 'INSPECTED', qr, 'SYSTEM'))

    # 4. Women Member & Guest: 83 lockers (024 -> 106)
    for i in range(24, 107):
        num = f"{i:03d}"
        l_id = f"W-MEM-{num}"
        qr = f"PHX-{l_id}-" + hashlib.md5(f"W_MEM_{num}_2026".encode()).hexdigest()[:8].upper()
        lockers_data.append((l_id, num, 'WOMEN', 'MEMBER_GUEST', 'INSPECTED', qr, 'SYSTEM'))

    cursor.executemany("""
    INSERT INTO lockers (locker_id, locker_number, zone_id, tier_id, current_status, qr_token, last_updated_by)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, lockers_data)

    conn.commit()
    print("✅ Đã khởi tạo thành công 603 tủ!")
else:
    print(f"Database đã có {count} tủ. Bỏ qua.")

conn.close()
