import cv2
import json
import time
import urllib.request
import urllib.error
import sys

# Windows beep sound support
try:
    import winsound
    def play_beep(success=True):
        if success:
            winsound.Beep(1000, 200) # Pleasant high beep
        else:
            winsound.Beep(300, 500) # Low buzz
except ImportError:
    # Fallback for non-Windows (or if winsound is not available)
    def play_beep(success=True):
        sys.stdout.write('\a')
        sys.stdout.flush()

def mark_attendance_api(user_code, api_url):
    """
    Sends the scanned QR code content to the local Flask web service.
    """
    data = json.dumps({'user_code': user_code}).encode('utf-8')
    req = urllib.request.Request(
        api_url, 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return True, res_data.get('message', 'Success'), res_data.get('data', {})
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode('utf-8'))
            return False, err_data.get('message', 'Server error.'), {}
        except:
            return False, f"HTTP Error {e.code}", {}
    except urllib.error.URLError as e:
        return False, f"Connection failed. Is the server running? ({e.reason})", {}

def run_scanner(api_url="http://127.0.0.1:5000/attendance/mark"):
    print("=" * 60)
    print("           ScanFlow Desktop OpenCV QR Scanner Client")
    print("=" * 60)
    print(f"Target API Endpoint: {api_url}")
    print("Press 'q' in the camera window to exit.")
    print("-" * 60)

    # Initialize video capture (0 is default built-in camera)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] Could not open webcam. Make sure no other app is using it.")
        return

    # Initialize OpenCV QR detector
    detector = cv2.QRCodeDetector()
    
    # Cooldown timer to avoid double scanning
    cooldown_until = 0
    
    # Text overlay state parameters
    status_text = "Scan QR Code"
    status_color = (255, 255, 255) # White
    status_expiry = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame from camera.")
            break
            
        # Flip frame horizontally for natural mirror feel
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Draw a scanner target frame in the center
        box_size = 220
        x_start = int((w - box_size) / 2)
        y_start = int((h - box_size) / 2)
        x_end = x_start + box_size
        y_end = y_start + box_size
        
        # Draw target rectangle bounding boxes
        cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (255, 255, 0), 2)
        cv2.putText(frame, "Align QR inside box", (x_start, y_start - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # Detect and decode QR Code
        current_time = time.time()
        if current_time > cooldown_until:
            # Detect QR code
            data, bbox, _ = detector.detectAndDecode(frame)
            
            if data:
                user_code = data.strip().upper()
                print(f"\n[SCAN] Detected QR code badge: {user_code}")
                
                # Highlight the QR code outline on camera output
                if bbox is not None and len(bbox) > 0:
                    pts = bbox[0].astype(int)
                    for i in range(len(pts)):
                        pt1 = tuple(pts[i])
                        pt2 = tuple(pts[(i + 1) % len(pts)])
                        cv2.line(frame, pt1, pt2, (0, 255, 0), 3)
                
                # Make API Call to mark attendance
                success, msg, details = mark_attendance_api(user_code, api_url)
                
                if success:
                    print(f"[SUCCESS] Attendance Logged: {details.get('name')} | {details.get('time')}")
                    play_beep(success=True)
                    status_text = f"GRANTED: {details.get('name')}"
                    status_color = (0, 255, 0) # Green in BGR
                else:
                    print(f"[DENIED] {msg}")
                    play_beep(success=False)
                    status_text = f"DENIED: {msg[:25]}"
                    status_color = (0, 0, 255) # Red in BGR
                
                # Set dynamic UI parameters
                status_expiry = current_time + 3.0 # Show text for 3 seconds
                cooldown_until = current_time + 3.0 # Cooldown scanner for 3 seconds
        
        # Draw dynamic status overlays
        if current_time < status_expiry:
            # Draw overlay banner behind text
            cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 0), -1)
            cv2.putText(frame, status_text, (20, h - 18), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        else:
            # Idle prompt
            cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 0), -1)
            cv2.putText(frame, "Scan QR Code Badge", (20, h - 18), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Draw a scanning bar animation overlay inside the box
        if current_time > cooldown_until:
            scan_line_y = y_start + int(((time.time() * 100) % box_size))
            cv2.line(frame, (x_start, scan_line_y), (x_end, scan_line_y), (0, 255, 255), 1)

        # Show camera output frame
        cv2.imshow("ScanFlow Attendance Terminal Scanner", frame)

        # Key check
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27: # Press 'q' or Esc to exit
            break

    # Release webcam and close window
    cap.release()
    cv2.destroyAllWindows()
    print("\nScanner terminal terminated. Have a good day!")

if __name__ == '__main__':
    # Allow overriding default API address via command arguments
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000/attendance/mark"
    run_scanner(url)
