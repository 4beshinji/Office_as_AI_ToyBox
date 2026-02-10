import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import TaskCard, { Task } from './components/TaskCard';

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/tasks/')
      .then(res => res.json())
      .then(data => {
        setTasks(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch tasks:", err);
        setLoading(false);
      });
  }, []);

  const handleAccept = (taskId: number) => {
    console.log('Accept task:', taskId);
    // TODO: Implement API call
  };

  const handleComplete = (taskId: number) => {
    console.log('Complete task:', taskId);
    // TODO: Implement API call
  };

  const handleIgnore = (taskId: number) => {
    console.log('Ignore task:', taskId);
    // TODO: Implement API call
  };

  return (
    <div className="min-h-screen bg-[var(--gray-50)]">
      {/* Header */}
      <header className="bg-white border-b border-[var(--gray-200)] elevation-1">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h1 className="text-4xl font-bold text-[var(--primary-500)]">
              SOMS ダッシュボード
            </h1>
            <p className="text-[var(--gray-600)] mt-1">
              共生型オフィス管理システム
            </p>
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-[var(--gray-900)] mb-2">
            利用可能なタスク
          </h2>
          <p className="text-[var(--gray-600)]">
            タスクを完了してオフィスクレジットを獲得し、快適なオフィス環境を維持しましょう
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-[var(--primary-500)] border-t-transparent"></div>
              <p className="text-[var(--gray-600)] mt-4">タスクを読み込み中...</p>
            </div>
          </div>
        ) : tasks.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[var(--gray-500)] text-lg">現在利用可能なタスクはありません。</p>
            <p className="text-[var(--gray-400)] text-sm mt-2">新しいタスクが追加されるまでお待ちください！</p>
          </div>
        ) : (
          <motion.div
            className="grid gap-4 md:grid-cols-1 lg:grid-cols-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {tasks.map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <TaskCard
                  task={task}
                  onAccept={handleAccept}
                  onComplete={handleComplete}
                  onIgnore={handleIgnore}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </main>
    </div>
  );
}

export default App;

