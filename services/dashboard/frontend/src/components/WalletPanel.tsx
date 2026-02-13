import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface Transaction {
  id: number;
  amount: number;
  description: string;
  created_at: string;
}

interface WalletPanelProps {
  userId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function WalletPanel({ userId, isOpen, onClose }: WalletPanelProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    if (!isOpen) return;
    fetch(`/api/wallet/wallets/${userId}/history?limit=20`)
      .then(res => res.json())
      .then(data => setTransactions(Array.isArray(data) ? data : []))
      .catch(() => setTransactions([]));
  }, [userId, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />
      <div className="relative w-80 bg-white shadow-xl p-6 overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-[var(--gray-900)]">ウォレット</h2>
          <button onClick={onClose} className="text-[var(--gray-400)] hover:text-[var(--gray-600)]">
            <X size={20} />
          </button>
        </div>
        {transactions.length === 0 ? (
          <p className="text-sm text-[var(--gray-500)]">取引履歴はありません</p>
        ) : (
          <ul className="space-y-2">
            {transactions.map(tx => (
              <li key={tx.id} className="text-sm border-b border-[var(--gray-100)] pb-2">
                <div className="flex justify-between">
                  <span className="text-[var(--gray-700)]">{tx.description}</span>
                  <span className={tx.amount >= 0 ? 'text-green-600' : 'text-red-500'}>
                    {tx.amount >= 0 ? '+' : ''}{tx.amount}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
