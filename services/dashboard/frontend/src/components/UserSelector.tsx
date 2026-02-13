import { useState, useEffect } from 'react';

export interface UserInfo {
  id: number;
  username: string;
  display_name?: string;
}

interface UserSelectorProps {
  currentUser: UserInfo | null;
  onSelect: (user: UserInfo | null) => void;
}

export default function UserSelector({ currentUser, onSelect }: UserSelectorProps) {
  const [users, setUsers] = useState<UserInfo[]>([]);

  useEffect(() => {
    fetch('/api/users/')
      .then(res => res.json())
      .then(setUsers)
      .catch(() => {});
  }, []);

  if (currentUser) {
    return (
      <span className="text-sm text-[var(--gray-700)] px-2 py-1 rounded bg-[var(--gray-100)]">
        {currentUser.display_name || currentUser.username}
      </span>
    );
  }

  return (
    <select
      className="text-sm border border-[var(--gray-300)] rounded px-2 py-1"
      value=""
      onChange={(e) => {
        const user = users.find(u => u.id === Number(e.target.value));
        if (user) onSelect(user);
      }}
    >
      <option value="">ユーザー選択</option>
      {users.map(u => (
        <option key={u.id} value={u.id}>
          {u.display_name || u.username}
        </option>
      ))}
    </select>
  );
}
