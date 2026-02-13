import { useState, useEffect } from 'react';
import { Coins } from 'lucide-react';

interface WalletBadgeProps {
  userId: number | null;
  onClick: () => void;
}

export default function WalletBadge({ userId, onClick }: WalletBadgeProps) {
  const [balance, setBalance] = useState<number | null>(null);

  useEffect(() => {
    if (!userId) { setBalance(null); return; }
    fetch(`/api/wallet/wallets/${userId}`)
      .then(res => res.json())
      .then(data => setBalance(data.balance ?? null))
      .catch(() => setBalance(null));
    const interval = setInterval(() => {
      fetch(`/api/wallet/wallets/${userId}`)
        .then(res => res.json())
        .then(data => setBalance(data.balance ?? null))
        .catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, [userId]);

  if (balance === null) return null;

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-yellow-100 to-amber-100 border border-[var(--gold)] text-sm font-medium text-[var(--gold-dark)] hover:shadow-sm transition-shadow"
    >
      <Coins size={14} />
      {balance} SOMS
    </button>
  );
}
