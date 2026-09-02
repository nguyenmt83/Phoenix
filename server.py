import http.server
import socketserver
import json
import urllib.parse
import os
import hashlib
import time
import threading
from datetime import datetime

PORT = int(os.environ.get('PORT', 8080))
DB_FILE = os.path.join(os.path.dirname(__file__), 'db.json')

# Global database structure
db_lock = threading.Lock()
sse_clients = []

def init_db():
    if not os.path.exists(DB_FILE):
        print("--- KHỞI TẠO CƠ SỞ DỮ LIỆU GLMS 603 TỦ ---")
        lockers = []
        
        # 1. Men VIP: 221 lockers (001 -> 221)
        for i in range(1, 222):
            num = f"{i:03d}"
            l_id = f"M-VIP-{num}"
            token = f"PHX-M-VIP-{num}-" + hashlib.md5(f"M_VIP_{num}_2026".encode()).hexdigest()[:8].upper()
            lockers.append({
                "locker_id": l_id, "locker_number": num, "zone_id": "MEN", "tier_id": "VIP",
                "current_status": "INSPECTED", "qr_token": token, "guest_name": "", "assigned_at": None,
                "last_changed": datetime.now().isoformat(), "updated_by": "SYSTEM", "notes": ""
            })
            
        # 2. Men Member & Guest: 276 lockers (222 -> 497)
        for i in range(222, 498):
            num = f"{i:03d}"
            l_id = f"M-MEM-{num}"
            token = f"PHX-M-MEM-{num}-" + hashlib.md5(f"M_MEM_{num}_2026".encode()).hexdigest()[:8].upper()
            lockers.append({
                "locker_id": l_id, "locker_number": num, "zone_id": "MEN", "tier_id": "MEMBER_GUEST",
                "current_status": "INSPECTED", "qr_token": token, "guest_name": "", "assigned_at": None,
                "last_changed": datetime.now().isoformat(), "updated_by": "SYSTEM", "notes": ""
            })

        # 3. Women VIP: 23 lockers (001 -> 023)
        for i in range(1, 24):
            num = f"{i:03d}"
            l_id = f"W-VIP-{num}"
            token = f"PHX-W-VIP-{num}-" + hashlib.md5(f"W_VIP_{num}_2026".encode()).hexdigest()[:8].upper()
            lockers.append({
                "locker_id": l_id, "locker_number": num, "zone_id": "WOMEN", "tier_id": "VIP",
                "current_status": "INSPECTED", "qr_token": token, "guest_name": "", "assigned_at": None,
                "last_changed": datetime.now().isoformat(), "updated_by": "SYSTEM", "notes": ""
            })

        # 4. Women Member & Guest: 83 lockers (024 -> 106)
        for i in range(24, 107):
            num = f"{i:03d}"
            l_id = f"W-MEM-{num}"
            token = f"PHX-W-MEM-{num}-" + hashlib.md5(f"W_MEM_{num}_2026".encode()).hexdigest()[:8].upper()
            lockers.append({
                "locker_id": l_id, "locker_number": num, "zone_id": "WOMEN", "tier_id": "MEMBER_GUEST",
                "current_status": "INSPECTED", "qr_token": token, "guest_name": "", "assigned_at": None,
                "last_changed": datetime.now().isoformat(), "updated_by": "SYSTEM", "notes": ""
            })

        data = {
            "lockers": lockers,
            "logs": [{
                "log_id": 1, "locker_id": "ALL", "old_status": None, "new_status": "INSPECTED",
                "action": "INIT_SYSTEM", "user": "SYSTEM", "note": "Khởi tạo hệ thống 603 tủ",
                "timestamp": datetime.now().isoformat()
            }],
            "lost_and_found": [],
            "holds": []
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Đã tạo file cơ sở dữ liệu db.json với 603 tủ!")

def get_db():
    with db_lock:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

def save_db(data):
    with db_lock:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def broadcast_event(event_type, payload):
    msg = f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
    dead_clients = []
    for client in sse_clients:
        try:
            client.wfile.write(msg.encode('utf-8'))
            client.wfile.flush()
        except Exception:
            dead_clients.append(client)
    for dc in dead_clients:
        if dc in sse_clients:
            sse_clients.remove(dc)

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), 'public'), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Realtime Server-Sent Events (SSE) Stream
        if parsed.path == '/api/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            sse_clients.append(self)
            self.wfile.write(b"data: {\"type\": \"CONNECTED\"}\n\n")
            self.wfile.flush()
            while True:
                time.sleep(15)
                try:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                except Exception:
                    break
            return

        # API: Lấy toàn bộ danh sách 603 tủ
        if parsed.path == '/api/lockers':
            data = get_db()
            self.send_json(200, data['lockers'])
            return

        # API: Lấy danh sách đồ bỏ quên
        if parsed.path == '/api/lost-and-found':
            data = get_db()
            self.send_json(200, data['lost_and_found'])
            return

        # API: Lấy lịch sử Logs (Audit Trail)
        if parsed.path == '/api/logs':
            data = get_db()
            self.send_json(200, data['logs'][-200:]) # Trả về 200 log mới nhất
            return

        # API: Báo cáo Thống kê Analytics
        if parsed.path == '/api/analytics':
            data = get_db()
            lockers = data['lockers']
            total = len(lockers)
            inspected = sum(1 for l in lockers if l['current_status'] == 'INSPECTED')
            in_use = sum(1 for l in lockers if l['current_status'] == 'IN_USE')
            dirty = sum(1 for l in lockers if l['current_status'] == 'DIRTY')
            reserved = sum(1 for l in lockers if l['current_status'] == 'RESERVED')
            ooo = sum(1 for l in lockers if l['current_status'] == 'OOO')
            
            stats = {
                "total": total,
                "inspected": inspected,
                "in_use": in_use,
                "dirty": dirty,
                "reserved": reserved,
                "ooo": ooo,
                "occupancy_rate": round((in_use / total) * 100, 1) if total > 0 else 0,
                "men_total": sum(1 for l in lockers if l['zone_id'] == 'MEN'),
                "women_total": sum(1 for l in lockers if l['zone_id'] == 'WOMEN'),
                "vip_total": sum(1 for l in lockers if l['tier_id'] == 'VIP'),
                "mem_total": sum(1 for l in lockers if l['tier_id'] == 'MEMBER_GUEST')
            }
            self.send_json(200, stats)
            return

        # Static files serving
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        payload = json.loads(body) if body else {}

        # 1. API: HK Quét QR hoàn tất dọn tủ
        if parsed.path == '/api/lockers/inspect-by-token':
            token = payload.get('qr_token', '').strip()
            user = payload.get('user', 'HK_Staff')
            data = get_db()
            
            locker = next((l for l in data['lockers'] if l['qr_token'] == token), None)
            if not locker:
                return self.send_json(404, {"success": False, "message": "Mã QR không tồn tại trong hệ thống!"})

            old_st = locker['current_status']
            locker['current_status'] = 'INSPECTED'
            locker['last_changed'] = datetime.now().isoformat()
            locker['updated_by'] = user
            locker['guest_name'] = ""

            log_entry = {
                "log_id": len(data['logs']) + 1,
                "locker_id": locker['locker_id'],
                "old_status": old_st,
                "new_status": "INSPECTED",
                "action": "HK_QR_INSPECT",
                "user": user,
                "note": f"Nhân viên {user} quét QR xác nhận tủ sạch",
                "timestamp": datetime.now().isoformat()
            }
            data['logs'].append(log_entry)
            save_db(data)

            # Phát sự kiện Realtime tới toàn bộ client
            broadcast_event('locker_updated', {
                "locker_id": locker['locker_id'],
                "new_status": "INSPECTED",
                "old_status": old_st,
                "updated_by": user,
                "timestamp": locker['last_changed']
            })

            return self.send_json(200, {"success": True, "message": f"Tủ {locker['locker_number']} đã chuyển sang SẴN SÀNG!", "locker": locker})

        # 2. API: Cập nhật trạng thái thủ công (FO Check-in / Check-out / OOO / Reserved)
        if parsed.path == '/api/lockers/update-status':
            l_id = payload.get('locker_id')
            new_st = payload.get('new_status')
            user = payload.get('user', 'FO_Desk')
            guest = payload.get('guest_name', '')
            note = payload.get('note', '')

            data = get_db()
            locker = next((l for l in data['lockers'] if l['locker_id'] == l_id), None)
            if not locker:
                return self.send_json(404, {"success": False, "message": "Không tìm thấy tủ!"})

            old_st = locker['current_status']
            locker['current_status'] = new_st
            locker['last_changed'] = datetime.now().isoformat()
            locker['updated_by'] = user
            if new_st == 'IN_USE':
                locker['guest_name'] = guest
                locker['assigned_at'] = datetime.now().isoformat()
            elif new_st in ['DIRTY', 'INSPECTED']:
                locker['guest_name'] = ""
                locker['assigned_at'] = None

            log_entry = {
                "log_id": len(data['logs']) + 1,
                "locker_id": locker['locker_id'],
                "old_status": old_st,
                "new_status": new_st,
                "action": f"FO_{new_st}",
                "user": user,
                "note": note or f"Cập nhật trạng thái sang {new_st}",
                "timestamp": datetime.now().isoformat()
            }
            data['logs'].append(log_entry)
            save_db(data)

            broadcast_event('locker_updated', {
                "locker_id": locker['locker_id'],
                "new_status": new_st,
                "old_status": old_st,
                "updated_by": user,
                "guest_name": locker['guest_name'],
                "timestamp": locker['last_changed']
            })

            return self.send_json(200, {"success": True, "locker": locker})

        # 3. API: Chuyển đổi tủ (Locker Swap / Transfer)
        if parsed.path == '/api/lockers/transfer':
            from_id = payload.get('from_locker_id')
            to_id = payload.get('to_locker_id')
            user = payload.get('user', 'FO_Desk')
            
            data = get_db()
            l_from = next((l for l in data['lockers'] if l['locker_id'] == from_id), None)
            l_to = next((l for l in data['lockers'] if l['locker_id'] == to_id), None)

            if not l_from or not l_to:
                return self.send_json(400, {"success": False, "message": "Không tìm thấy tủ nguồn hoặc tủ đích!"})
            if l_to['current_status'] != 'INSPECTED':
                return self.send_json(400, {"success": False, "message": "Tủ đích chưa sẵn sàng (phải ở trạng thái Inspected)!"})

            guest = l_from['guest_name']
            l_from['current_status'] = 'DIRTY'
            l_from['guest_name'] = ''
            l_from['last_changed'] = datetime.now().isoformat()
            
            l_to['current_status'] = 'IN_USE'
            l_to['guest_name'] = guest
            l_to['assigned_at'] = datetime.now().isoformat()
            l_to['last_changed'] = datetime.now().isoformat()

            data['logs'].append({
                "log_id": len(data['logs']) + 1, "locker_id": f"{from_id}->{to_id}",
                "old_status": "SWAP", "new_status": "SWAP", "action": "TRANSFER_GUEST",
                "user": user, "note": f"Chuyển khách {guest} từ tủ {from_id} sang tủ {to_id}",
                "timestamp": datetime.now().isoformat()
            })
            save_db(data)

            broadcast_event('locker_updated', {"locker_id": from_id, "new_status": "DIRTY", "updated_by": user})
            broadcast_event('locker_updated', {"locker_id": to_id, "new_status": "IN_USE", "guest_name": guest, "updated_by": user})

            return self.send_json(200, {"success": True, "message": f"Đã chuyển khách sang tủ {to_id} thành công!"})

        # 4. API: Báo cáo Đồ bỏ quên (Lost & Found)
        if parsed.path == '/api/lost-and-found':
            l_id = payload.get('locker_id')
            desc = payload.get('item_description', '')
            found_by = payload.get('found_by', 'HK_Staff')

            data = get_db()
            item = {
                "item_id": len(data['lost_and_found']) + 1,
                "locker_id": l_id,
                "description": desc,
                "found_by": found_by,
                "status": "PENDING",
                "created_at": datetime.now().isoformat()
            }
            data['lost_and_found'].append(item)
            
            data['logs'].append({
                "log_id": len(data['logs']) + 1, "locker_id": l_id,
                "old_status": None, "new_status": "LOST_FOUND", "action": "REPORT_LOST_ITEM",
                "user": found_by, "note": f"Phát hiện đồ bỏ quên tại tủ {l_id}: {desc}",
                "timestamp": datetime.now().isoformat()
            })
            save_db(data)

            broadcast_event('lost_found_reported', item)
            return self.send_json(200, {"success": True, "message": "Đã gửi thông báo đồ bỏ quên tới Lễ tân!", "item": item})

        # 5. API: Trả đồ bỏ quên cho khách
        if parsed.path == '/api/lost-and-found/return':
            item_id = payload.get('item_id')
            user = payload.get('user', 'FO_Desk')
            data = get_db()
            
            item = next((i for i in data['lost_and_found'] if i['item_id'] == item_id), None)
            if item:
                item['status'] = 'RETURNED'
                item['returned_by'] = user
                item['returned_at'] = datetime.now().isoformat()
                save_db(data)
                broadcast_event('lost_found_updated', item)
                return self.send_json(200, {"success": True, "message": "Đã xác nhận trả đồ cho khách!"})
            return self.send_json(404, {"success": False, "message": "Không tìm thấy đồ vật!"})

        # 6. API Admin: Quét ghép nối lại mã QR (Remap)
        if parsed.path == '/api/admin/remap-qr':
            target_id = payload.get('target_locker_id')
            new_token = payload.get('new_qr_token')
            user = payload.get('user', 'IT_Admin')

            data = get_db()
            # Xóa gán cũ nếu token này đang ở tủ khác
            for l in data['lockers']:
                if l['qr_token'] == new_token:
                    l['qr_token'] = f"OLD_{l['locker_id']}_{int(time.time())}"

            target = next((l for l in data['lockers'] if l['locker_id'] == target_id), None)
            if not target:
                return self.send_json(404, {"success": False, "message": "Không tìm thấy tủ mục tiêu!"})

            target['qr_token'] = new_token
            data['logs'].append({
                "log_id": len(data['logs']) + 1, "locker_id": target_id,
                "old_status": "CONFIG", "new_status": "CONFIG", "action": "ADMIN_REMAP_QR",
                "user": user, "note": f"Gán lại mã QR mới: {new_token}",
                "timestamp": datetime.now().isoformat()
            })
            save_db(data)
            return self.send_json(200, {"success": True, "message": f"Đã ghép nối mã QR mới cho tủ {target_id} thành công!"})

        self.send_json(404, {"error": "Endpoint not found"})

    def send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    init_db()
    server = socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"🚀 GLMS Server đang chạy tại: http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang tắt server...")
        server.server_close()
