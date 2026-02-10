import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import TaskCard, { Task } from './components/TaskCard';

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  // Configuration
  const MAX_DISPLAY_TASKS = 10;
  const COMPLETED_Display_SECONDS = 300; // 5 minutes

  useEffect(() => {
    const fetchTasks = () => {
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
    };

    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);

    return () => clearInterval(interval);
  }, []);

  // Sort and Filter Tasks
  const visibleTasks = tasks
    .filter(task => {
      // Filter out completed tasks older than config time
      if (task.is_completed && task.completed_at) {
        const completedTime = new Date(task.completed_at).getTime();
        const now = new Date().getTime();
        return (now - completedTime) / 1000 < COMPLETED_Display_SECONDS;
      }
      return true;
    })
    .sort((a, b) => {
      // 1. Active tasks first
      if (a.is_completed !== b.is_completed) {
        return a.is_completed ? 1 : -1;
      }
      // 2. Sort by creation date (Newest first)
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    })
    .slice(0, MAX_DISPLAY_TASKS);

  const handleAccept = (taskId: number) => {
    console.log('Accept task:', taskId);
    // TODO: Implement API call
  };

  const handleComplete = (taskId: number) => {
    console.log('Complete task:', taskId);
    fetch(`/api/tasks/${taskId}/complete`, {
      method: 'PUT',
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to complete task');
        return res.json();
      })
      .then(updatedTask => {
        setTasks(tasks.map(t => t.id === taskId ? updatedTask : t));
      })
      .catch(err => console.error("Error completing task:", err));
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
            お願い事一覧
          </h2>
          <p className="text-[var(--gray-600)]">
            タスクを完了して神保ポイントを獲得し、快適なオフィス環境を維持しましょう
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
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {visibleTasks.map((task, index) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
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

