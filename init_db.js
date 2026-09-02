const sqlite3 = require('sqlite3').verbose();
const crypto = require('crypto');
const path = require('path');

const dbPath = path.join(__dirname, 'locker.db');
const db = new sqlite3.Database(dbPath);

db.serialize(() => {
  console.log('--- KHỞI TẠO CƠ SỞ DỮ LIỆU GLMS PHOENIX GOLF ---');

  // 1. Zones
  db.run(`CREATE TABLE IF NOT EXISTS locker_zones (
    zone_id TEXT PRIMARY KEY,
    zone_name TEXT NOT NULL,
    gender TEXT NOT NULL
  )`);

  // 2. Tiers
  db.run(`CREATE TABLE IF NOT EXISTS locker_tiers (
    tier_id TEXT PRIMARY KEY,
    tier_name TEXT NOT NULL,
    badge_label TEXT NOT NULL
  )`);

  // 3. Statuses
  db.run(`CREATE TABLE IF NOT EXISTS locker_statuses (
    status_id TEXT PRIMARY KEY,
    status_name TEXT NOT NULL,
    color_code TEXT NOT NULL
  )`);

  // 4. Lockers
  db.run(`CREATE TABLE IF NOT EXISTS lockers (
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
  )`);

  // 5. History Logs (Audit Trail)
  db.run(`CREATE TABLE IF NOT EXISTS locker_history_logs (
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
  )`);

  // 6. Lost & Found Items
  db.run(`CREATE TABLE IF NOT EXISTS lost_and_found_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locker_id TEXT NOT NULL,
    item_description TEXT NOT NULL,
    image_data TEXT,
    found_by TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING', -- 'PENDING', 'RETURNED'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    returned_at DATETIME,
    returned_by TEXT
  )`);

  // 7. Long-term Member Holds
  db.run(`CREATE TABLE IF NOT EXISTS long_term_holds (
    hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
    locker_id TEXT UNIQUE NOT NULL,
    member_name TEXT NOT NULL,
    member_card_no TEXT,
    phone_number TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // --- SEEDING DATA ---
  // Seed Zones
  db.run(`INSERT OR REPLACE INTO locker_zones (zone_id, zone_name, gender) VALUES 
    ('MEN', 'Khu Vực Nam', 'MEN'),
    ('WOMEN', 'Khu Vực Nữ', 'WOMEN')`);

  // Seed Tiers
  db.run(`INSERT OR REPLACE INTO locker_tiers (tier_id, tier_name, badge_label) VALUES 
    ('VIP', 'Hạng VIP', '★ VIP'),
    ('MEMBER_GUEST', 'Hạng Member & Guest', 'M&G')`);

  // Seed Statuses
  db.run(`INSERT OR REPLACE INTO locker_statuses (status_id, status_name, color_code) VALUES 
    ('INSPECTED', 'Sẵn sàng (Đã dọn)', '#198754'),
    ('IN_USE', 'Đang sử dụng', '#DC3545'),
    ('DIRTY', 'Chờ dọn (Dirty)', '#FFC107'),
    ('RESERVED', 'Member giữ tủ', '#6F42C1'),
    ('OOO', 'Bảo trì / Hỏng', '#6C757D')`);

  // Check if lockers table already has data
  db.get(`SELECT COUNT(*) as count FROM lockers`, (err, row) => {
    if (err) return console.error(err);
    if (row.count === 0) {
      console.log('Đang nạp danh mục chuẩn 603 tủ...');
      const stmt = db.prepare(`INSERT INTO lockers (locker_id, locker_number, zone_id, tier_id, current_status, qr_token, last_updated_by) VALUES (?, ?, ?, ?, ?, ?, ?)`);

      // 1. Men VIP: 221 lockers (001 -> 221)
      for (let i = 1; i <= 221; i++) {
        const num = String(i).padStart(3, '0');
        const id = `M-VIP-${num}`;
        const token = `PHX-M-VIP-${num}-` + crypto.createHash('md5').update(`M_VIP_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
        stmt.run(id, num, 'MEN', 'VIP', 'INSPECTED', token, 'INIT_SEED');
      }

      // 2. Men Member & Guest: 276 lockers (222 -> 497)
      for (let i = 222; i <= 497; i++) {
        const num = String(i).padStart(3, '0');
        const id = `M-MEM-${num}`;
        const token = `PHX-M-MEM-${num}-` + crypto.createHash('md5').update(`M_MEM_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
        stmt.run(id, num, 'MEN', 'MEMBER_GUEST', 'INSPECTED', token, 'INIT_SEED');
      }

      // 3. Women VIP: 23 lockers (001 -> 023)
      for (let i = 1; i <= 23; i++) {
        const num = String(i).padStart(3, '0');
        const id = `W-VIP-${num}`;
        const token = `PHX-W-VIP-${num}-` + crypto.createHash('md5').update(`W_VIP_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
        stmt.run(id, num, 'WOMEN', 'VIP', 'INSPECTED', token, 'INIT_SEED');
      }

      // 4. Women Member & Guest: 83 lockers (024 -> 106)
      for (let i = 24; i <= 106; i++) {
        const num = String(i).padStart(3, '0');
        const id = `W-MEM-${num}`;
        const token = `PHX-W-MEM-${num}-` + crypto.createHash('md5').update(`W_MEM_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
        stmt.run(id, num, 'WOMEN', 'MEMBER_GUEST', 'INSPECTED', token, 'INIT_SEED');
      }

      stmt.finalize();
      console.log('✅ Khởi tạo thành công 603 tủ (Nam: 221 VIP + 276 Mem | Nữ: 23 VIP + 83 Mem)!');
    } else {
      console.log(`Database đã có sẵn ${row.count} tủ. Bỏ qua bước seed dữ liệu.`);
    }
  });
});

db.close();
