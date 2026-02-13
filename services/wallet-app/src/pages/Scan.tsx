import { useRef, useEffect, useState, useCallback } from 'react';
import { claimTaskReward } from '../api/wallet';

interface ScanProps {
  userId: number;
}

interface QRPayload {
  task_id: number;
  amount: number;
}

function parseQR(text: string): QRPayload | null {
  try {
    const url = new URL(text);
    if (url.protocol !== 'soms:' || url.hostname !== 'reward') return null;
    const taskId = parseInt(url.searchParams.get('task_id') || '', 10);
    const amount = parseInt(url.searchParams.get('amount') || '', 10);
    if (isNaN(taskId) || isNaN(amount)) return null;
    return { task_id: taskId, amount };
  } catch {
    return null;
  }
}

export default function Scan({ userId }: ScanProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<'idle' | 'scanning' | 'claiming' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setStatus('scanning');
      setCameraError(null);
    } catch {
      setCameraError('Camera access denied. Please allow camera permissions.');
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => {
    startCamera();
    return stopCamera;
  }, [startCamera, stopCamera]);

  // BarcodeDetector-based scanning
  useEffect(() => {
    if (status !== 'scanning') return;

    const detector = 'BarcodeDetector' in window
      ? new (window as unknown as { BarcodeDetector: new (opts: { formats: string[] }) => { detect: (src: HTMLVideoElement) => Promise<{ rawValue: string }[]> } }).BarcodeDetector({ formats: ['qr_code'] })
      : null;

    if (!detector) {
      setMessage('QR scanning requires BarcodeDetector API (Chrome/Edge).');
      return;
    }

    let running = true;
    async function scan() {
      while (running && videoRef.current) {
        try {
          const barcodes = await detector!.detect(videoRef.current);
          for (const barcode of barcodes) {
            const payload = parseQR(barcode.rawValue);
            if (payload) {
              running = false;
              setStatus('claiming');
              setMessage(`Claiming ${(payload.amount / 1000).toFixed(3)} SOMS...`);
              try {
                await claimTaskReward(userId, payload.task_id, payload.amount);
                setStatus('success');
                setMessage(`Received ${(payload.amount / 1000).toFixed(3)} SOMS!`);
              } catch (e) {
                setStatus('error');
                setMessage(e instanceof Error ? e.message : 'Claim failed');
              }
              return;
            }
          }
        } catch { /* ignore detect errors */ }
        await new Promise(r => setTimeout(r, 300));
      }
    }

    scan();
    return () => { running = false; };
  }, [status, userId]);

  const handleReset = () => {
    setStatus('idle');
    setMessage('');
    startCamera();
  };

  return (
    <div className="p-4 pb-24 space-y-4">
      <h1 className="text-xl font-bold">QR Scan</h1>
      <p className="text-sm text-gray-400">Scan a task QR code to claim rewards.</p>

      <div className="relative rounded-2xl overflow-hidden bg-black aspect-square">
        <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
        <canvas ref={canvasRef} className="hidden" />
        {status === 'scanning' && (
          <div className="absolute inset-0 border-2 border-amber-400/50 rounded-2xl pointer-events-none">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border-2 border-amber-400 rounded-lg" />
          </div>
        )}
      </div>

      {cameraError && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-sm text-red-300">
          {cameraError}
        </div>
      )}

      {message && (
        <div className={`rounded-lg p-3 text-sm ${
          status === 'success' ? 'bg-emerald-900/30 border border-emerald-700 text-emerald-300' :
          status === 'error' ? 'bg-red-900/30 border border-red-700 text-red-300' :
          'bg-gray-800 text-gray-300'
        }`}>
          {message}
        </div>
      )}

      {(status === 'success' || status === 'error') && (
        <button
          onClick={handleReset}
          className="w-full py-3 bg-amber-500 text-black font-semibold rounded-xl"
        >
          Scan Again
        </button>
      )}
    </div>
  );
}
