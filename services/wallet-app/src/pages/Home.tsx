import { useEffect, useState } from 'react';
import { getWallet, getHistory, getSupply, type Wallet, type LedgerEntry, type SupplyStats } from '../api/wallet';
import BalanceCard from '../components/BalanceCard';
import TransactionItem from '../components/TransactionItem';

interface HomeProps {
  userId: number;
}

export default function Home({ userId }: HomeProps) {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [recent, setRecent] = useState<LedgerEntry[]>([]);
  const [supply, setSupply] = useState<SupplyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [w, h, s] = await Promise.all([
          getWallet(userId),
          getHistory(userId, 3),
          getSupply(),
        ]);
        if (cancelled) return;
        setWallet(w);
        setRecent(h);
        setSupply(s);
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Load failed');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, 15000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [userId]);

  return (
    <div className="p-4 pb-24 space-y-6">
      <BalanceCard balance={wallet?.balance ?? 0} loading={loading} />

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {supply && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-900 rounded-xl p-3 text-center">
            <p className="text-xs text-gray-500">Issued</p>
            <p className="text-sm font-semibold text-gray-300">{(supply.total_issued / 1000).toFixed(1)}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-3 text-center">
            <p className="text-xs text-gray-500">Burned</p>
            <p className="text-sm font-semibold text-red-400">{(supply.total_burned / 1000).toFixed(1)}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-3 text-center">
            <p className="text-xs text-gray-500">Circulating</p>
            <p className="text-sm font-semibold text-amber-400">{(supply.circulating / 1000).toFixed(1)}</p>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-2">Recent Activity</h2>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-14 bg-gray-900 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : recent.length === 0 ? (
          <p className="text-gray-500 text-sm">No transactions yet.</p>
        ) : (
          <div className="bg-gray-900 rounded-xl px-4">
            {recent.map(entry => (
              <TransactionItem key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
