const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

const PORT = process.env.PORT || 8080;
const DB_FILE = path.join(__dirname, 'db.json');

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Khởi tạo Database nếu chưa có
function initDB() {
  if (!fs.existsSync(DB_FILE)) {
    console.log("Khởi tạo db.json cho 603 tủ...");
    const lockers = [];
    // 1. Nam VIP: 221 (001 -> 221)
    for (let i = 1; i <= 221; i++) {
      const num = String(i).padStart(3, '0');
      const id = `M-VIP-${num}`;
      const token = `PHX-M-VIP-${num}-` + crypto.createHash('md5').update(`M_VIP_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
      lockers.push({ locker_id: id, locker_number: num, zone_id: 'MEN', tier_id: 'VIP', current_status: 'INSPECTED', qr_token: token, guest_name: '', last_changed: new Date().toISOString() });
    }
    // 2. Nam Member: 276 (222 -> 497)
    for (let i = 222; i <= 497; i++) {
      const num = String(i).padStart(3, '0');
      const id = `M-MEM-${num}`;
      const token = `PHX-M-MEM-${num}-` + crypto.createHash('md5').update(`M_MEM_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
      lockers.push({ locker_id: id, locker_number: num, zone_id: 'MEN', tier_id: 'MEMBER_GUEST', current_status: 'INSPECTED', qr_token: token, guest_name: '', last_changed: new Date().toISOString() });
    }
    // 3. Nữ VIP: 23 (001 -> 023)
    for (let i = 1; i <= 23; i++) {
      const num = String(i).padStart(3, '0');
      const id = `W-VIP-${num}`;
      const token = `PHX-W-VIP-${num}-` + crypto.createHash('md5').update(`W_VIP_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
      lockers.push({ locker_id: id, locker_number: num, zone_id: 'WOMEN', tier_id: 'VIP', current_status: 'INSPECTED', qr_token: token, guest_name: '', last_changed: new Date().toISOString() });
    }
    // 4. Nữ Member: 83 (024 -> 106)
    for (let i = 24; i <= 106; i++) {
      const num = String(i).padStart(3, '0');
      const id = `W-MEM-${num}`;
      const token = `PHX-W-MEM-${num}-` + crypto.createHash('md5').update(`W_MEM_${num}_2026`).digest('hex').substring(0, 8).toUpperCase();
      lockers.push({ locker_id: id, locker_number: num, zone_id: 'WOMEN', tier_id: 'MEMBER_GUEST', current_status: 'INSPECTED', qr_token: token, guest_name: '', last_changed: new Date().toISOString() });
    }

    const data = {
      lockers,
      logs: [{ log_id: 1, locker_id: 'ALL', old_status: null, new_status: 'INSPECTED', action: 'INIT_SYSTEM', user: 'SYSTEM', note: 'Khởi tạo 603 tủ', timestamp: new Date().toISOString() }],
      lost_and_found: []
    };
    fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf-8');
  }
}

function getDB() { return JSON.parse(fs.readFileSync(DB_FILE, 'utf-8')); }
function saveDB(data) { fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), 'utf-8'); }

// APIs
app.get('/api/lockers', (req, res) => res.json(getDB().lockers));
app.get('/api/logs', (req, res) => res.json(getDB().logs.slice(-200)));
app.get('/api/lost-and-found', (req, res) => res.json(getDB().lost_and_found));

app.get('/api/analytics', (req, res) => {
  const lockers = getDB().lockers;
  const total = lockers.length;
  const in_use = lockers.filter(l => l.current_status === 'IN_USE').length;
  res.json({
    total,
    inspected: lockers.filter(l => l.current_status === 'INSPECTED').length,
    in_use,
    dirty: lockers.filter(l => l.current_status === 'DIRTY').length,
    reserved: lockers.filter(l => l.current_status === 'RESERVED').length,
    ooo: lockers.filter(l => l.current_status === 'OOO').length,
    occupancy_rate: total > 0 ? Math.round((in_use / total) * 1000) / 10 : 0
  });
});

app.post('/api/lockers/inspect-by-token', (req, res) => {
  const { qr_token, user = 'HK_Staff' } = req.body;
  const data = getDB();
  const locker = data.lockers.find(l => l.qr_token === qr_token);
  if (!locker) return res.status(404).json({ success: false, message: 'Mã QR không hợp lệ' });

  const old_st = locker.current_status;
  locker.current_status = 'INSPECTED';
  locker.last_changed = new Date().toISOString();
  locker.updated_by = user;
  locker.guest_name = '';

  data.logs.push({ log_id: data.logs.length + 1, locker_id: locker.locker_id, old_status: old_st, new_status: 'INSPECTED', action: 'HK_QR_INSPECT', user, note: `Quét QR bởi ${user}`, timestamp: new Date().toISOString() });
  saveDB(data);

  io.emit('locker_updated', { locker_id: locker.locker_id, new_status: 'INSPECTED', old_status: old_st, updated_by: user });
  res.json({ success: true, message: `Tủ ${locker.locker_number} đã sẵn sàng!`, locker });
});

app.post('/api/lockers/update-status', (req, res) => {
  const { locker_id, new_status, user = 'FO_Desk', guest_name = '', note = '' } = req.body;
  const data = getDB();
  const locker = data.lockers.find(l => l.locker_id === locker_id);
  if (!locker) return res.status(404).json({ success: false, message: 'Không tìm thấy tủ' });

  const old_st = locker.current_status;
  locker.current_status = new_status;
  locker.last_changed = new Date().toISOString();
  locker.updated_by = user;
  if (new_status === 'IN_USE') locker.guest_name = guest_name;
  else if (['DIRTY', 'INSPECTED'].includes(new_status)) locker.guest_name = '';

  data.logs.push({ log_id: data.logs.length + 1, locker_id: locker.locker_id, old_status: old_st, new_status, action: `FO_${new_status}`, user, note, timestamp: new Date().toISOString() });
  saveDB(data);

  io.emit('locker_updated', { locker_id: locker.locker_id, new_status, old_status: old_st, guest_name: locker.guest_name, updated_by: user });
  res.json({ success: true, locker });
});

initDB();
server.listen(PORT, () => console.log(`🚀 GLMS Node.js Server đang chạy tại port ${PORT}`));
