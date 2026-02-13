import { useState, useEffect, useCallback, useRef } from 'react';
import { X, Send } from 'lucide-react';

interface Transaction {
  id: number;
  amount: number;
  description: string;
  transaction_type: string;
  created_at: string;
}

interface UserOption {
  id: number;
  username: string;
  display_name?: string;
}

interface FeeInfo {
  fee_rate: number;
  fee_amount: number;
  net_amount: number;
  min_transfer: number;
  below_minimum: boolean;
}

interface WalletPanelProps {
  userId: number;
  isOpen: boolean;
  onClose: () => void;
}

const TX_TYPE_LABELS: Record<string, string> = {
  FEE_BURN: '手数料',
  DEMURRAGE: '滞留税',
  TASK_REWARD: 'タスク報酬',
  P2P_TRANSFER: '送金',
};

export default function WalletPanel({ userId, isOpen, onClose }: WalletPanelProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [toUserId, setToUserId] = useState('');
  const [amount, setAmount] = useState('');
  const [transferMsg, setTransferMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [sending, setSending] = useState(false);
  const [feeInfo, setFeeInfo] = useState<FeeInfo | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchHistory = useCallback(() => {
    fetch(`/api/wallet/wallets/${userId}/history?limit=20`)
      .then(res => res.json())
      .then(data => setTransactions(Array.isArray(data) ? data : []))
      .catch(() => setTransactions([]));
  }, [userId]);

  useEffect(() => {
    if (!isOpen) return;
    fetchHistory();
    fetch('/api/users/')
      .then(res => res.json())
      .then((data: UserOption[]) => setUsers(data.filter(u => u.id !== userId)))
      .catch(() => setUsers([]));
  }, [userId, isOpen, fetchHistory]);

  // Debounced fee preview
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    const num = parseInt(amount, 10);
    if (!amount || isNaN(num) || num <= 0) {
      setFeeInfo(null);
      return;
    }

    debounceRef.current = setTimeout(() => {
      fetch(`/api/wallet/transactions/transfer-fee?amount=${num}`)
        .then(res => res.json())
        .then((data: FeeInfo) => setFeeInfo(data))
        .catch(() => setFeeInfo(null));
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [amount]);

  const handleTransfer = async () => {
    if (!toUserId || !amount) return;
    const amountNum = parseInt(amount, 10);
    if (isNaN(amountNum) || amountNum <= 0) {
      setTransferMsg({ ok: false, text: '金額は正の整数を入力してください' });
      return;
    }

    setSending(true);
    setTransferMsg(null);
    try {
      const res = await fetch('/api/wallet/transactions/p2p-transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_user_id: userId,
          to_user_id: parseInt(toUserId, 10),
          amount: amountNum,
          description: '送金',
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'エラーが発生しました' }));
        setTransferMsg({ ok: false, text: err.detail || 'エラー' });
      } else {
        const data = await res.json();
        const fee = data.fee?.fee_amount ?? 0;
        setTransferMsg({
          ok: true,
          text: `${amountNum} SOMS を送金しました (手数料: ${fee} SOMS)`,
        });
        setAmount('');
        setToUserId('');
        setFeeInfo(null);
        fetchHistory();
      }
    } catch {
      setTransferMsg({ ok: false, text: '通信エラー' });
    } finally {
      setSending(false);
    }
  };

  if (!isOpen) return null;

  const belowMin = feeInfo?.below_minimum ?? false;

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

        {/* Transfer form */}
        <div className="mb-6 p-3 bg-[var(--gray-50)] rounded-lg">
          <h3 className="text-sm font-semibold text-[var(--gray-700)] mb-2">送金</h3>
          <select
            className="w-full text-sm border border-[var(--gray-300)] rounded px-2 py-1.5 mb-2"
            value={toUserId}
            onChange={e => setToUserId(e.target.value)}
          >
            <option value="">送り先を選択</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>
                {u.display_name || u.username}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <input
              type="number"
              min="1"
              placeholder="金額"
              className="flex-1 text-sm border border-[var(--gray-300)] rounded px-2 py-1.5"
              value={amount}
              onChange={e => setAmount(e.target.value)}
            />
            <button
              onClick={handleTransfer}
              disabled={sending || !toUserId || !amount || belowMin}
              className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send size={14} />
              送金
            </button>
          </div>

          {/* Fee preview */}
          {feeInfo && (
            <div className="mt-2 text-xs text-[var(--gray-500)] space-y-0.5">
              <p>手数料: {feeInfo.fee_amount} SOMS ({(feeInfo.fee_rate * 100).toFixed(0)}%)</p>
              <p>合計負担: {feeInfo.net_amount + feeInfo.fee_amount} SOMS</p>
              <p>最低送金額: {feeInfo.min_transfer} SOMS</p>
              {belowMin && (
                <p className="text-red-500 font-medium">
                  最低送金額を下回っています
                </p>
              )}
            </div>
          )}

          {transferMsg && (
            <p className={`text-xs mt-1.5 ${transferMsg.ok ? 'text-green-600' : 'text-red-500'}`}>
              {transferMsg.text}
            </p>
          )}
        </div>

        {/* Transaction history */}
        <h3 className="text-sm font-semibold text-[var(--gray-700)] mb-2">取引履歴</h3>
        {transactions.length === 0 ? (
          <p className="text-sm text-[var(--gray-500)]">取引履歴はありません</p>
        ) : (
          <ul className="space-y-2">
            {transactions.map(tx => (
              <li key={tx.id} className="text-sm border-b border-[var(--gray-100)] pb-2">
                <div className="flex justify-between">
                  <span className="text-[var(--gray-700)]">
                    {TX_TYPE_LABELS[tx.transaction_type]
                      ? `[${TX_TYPE_LABELS[tx.transaction_type]}] `
                      : ''}
                    {tx.description}
                  </span>
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
