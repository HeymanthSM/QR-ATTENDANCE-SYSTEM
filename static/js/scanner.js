// QR Code Browser Scanner Integration using html5-qrcode
document.addEventListener('DOMContentLoaded', () => {
    let html5QrcodeScanner = null;
    let isProcessing = false;

    const scannerContainer = document.getElementById('scanner-card');
    const resultContainer = document.getElementById('scan-result-card');
    const resultBody = document.getElementById('scan-result-body');
    const startScannerBtn = document.getElementById('start-scanner-btn');
    const stopScannerBtn = document.getElementById('stop-scanner-btn');

    // Soft beep sound generator using Web Audio API (No files needed!)
    function playBeep(success = true) {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            if (success) {
                // High pleasant beep for success
                oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5 note
                gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
                oscillator.start();
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                oscillator.stop(audioCtx.currentTime + 0.15);
            } else {
                // Low buzzer sound for error
                oscillator.frequency.setValueAtTime(220, audioCtx.currentTime); // A3 note
                gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime);
                oscillator.start();
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                oscillator.stop(audioCtx.currentTime + 0.3);
            }
        } catch (e) {
            console.warn('Audio Context not allowed or supported yet: ', e);
        }
    }

    // Success callback when code is detected
    function onScanSuccess(decodedText, decodedResult) {
        if (isProcessing) return;
        
        isProcessing = true;
        console.log(`Scan result: ${decodedText}`);

        // Temporarily pause scanner by clearing it or halting requests
        if (html5QrcodeScanner) {
            html5QrcodeScanner.pause(true);
        }

        // Send scan to server
        fetch('/attendance/mark', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_code: decodedText })
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200 && body.success) {
                // Play success sound
                playBeep(true);
                showScanResult(true, body.data);
            } else {
                // Play error sound
                playBeep(false);
                showScanResult(false, null, body.message || 'Verification failed.');
            }
        })
        .catch(err => {
            console.error('API Error: ', err);
            playBeep(false);
            showScanResult(false, null, 'Server connection failure.');
        })
        .finally(() => {
            // Resume scanner after 3 seconds
            setTimeout(() => {
                isProcessing = false;
                if (html5QrcodeScanner) {
                    html5QrcodeScanner.resume();
                }
                // Hide result panel after a delay to get ready for next scan
                resultContainer.classList.add('d-none');
            }, 3000);
        });
    }

    function showScanResult(isSuccess, data, errorMsg = '') {
        resultContainer.classList.remove('d-none');
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        if (isSuccess) {
            resultContainer.className = 'card glass-card border-success mt-4 animate__animated animate__fadeIn';
            resultBody.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="me-3 bg-success bg-opacity-10 p-3 rounded-circle text-success">
                        <i class="bi bi-patch-check-fill fs-2"></i>
                    </div>
                    <div>
                        <h5 class="text-success mb-1 fw-bold">Scan Successful!</h5>
                        <p class="mb-0 text-secondary">Attendance marked for:</p>
                        <h4 class="mb-1 fw-bold">${data.name}</h4>
                        <span class="badge badge-present mb-2">${data.user_code}</span>
                        <div class="small text-muted">
                            <strong>Dept:</strong> ${data.department} | <strong>Time:</strong> ${data.time}
                        </div>
                    </div>
                </div>
            `;
        } else {
            resultContainer.className = 'card glass-card border-danger mt-4 animate__animated animate__fadeIn';
            resultBody.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="me-3 bg-danger bg-opacity-10 p-3 rounded-circle text-danger">
                        <i class="bi bi-exclamation-triangle-fill fs-2"></i>
                    </div>
                    <div>
                        <h5 class="text-danger mb-1 fw-bold">Scan Denied</h5>
                        <p class="mb-0">${errorMsg}</p>
                    </div>
                </div>
            `;
        }
    }

    function startScanning() {
        startScannerBtn.classList.add('d-none');
        stopScannerBtn.classList.remove('d-none');
        
        // Initialize the scanner object
        html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", 
            { 
                fps: 10, 
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            },
            /* verbose= */ false
        );
        
        html5QrcodeScanner.render(onScanSuccess, (err) => {
            // Suppress verbose error logging from library scanning frame failures
        });
    }

    function stopScanning() {
        if (html5QrcodeScanner) {
            html5QrcodeScanner.clear().then(() => {
                html5QrcodeScanner = null;
                startScannerBtn.classList.remove('d-none');
                stopScannerBtn.classList.add('d-none');
                resultContainer.classList.add('d-none');
            }).catch(err => {
                console.error("Failed to stop scanner: ", err);
            });
        }
    }

    if (startScannerBtn) {
        startScannerBtn.addEventListener('click', startScanning);
    }
    if (stopScannerBtn) {
        stopScannerBtn.addEventListener('click', stopScanning);
    }
});
