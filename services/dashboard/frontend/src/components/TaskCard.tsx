import { motion } from 'framer-motion';
import { MapPin, Coins, Circle, AlertCircle, AlertTriangle } from 'lucide-react';
import Card from './ui/Card';
import Badge from './ui/Badge';
import Button from './ui/Button';

export interface Task {
    id: number;
    title: string;
    description: string;
    location?: string;
    bounty_gold: number;
    urgency: number;
    is_completed: boolean;
    announcement_audio_url?: string;
    announcement_text?: string;
    completion_audio_url?: string;
    completion_text?: string;
    created_at: string;
    completed_at?: string;
    task_type?: string[];
}

interface TaskCardProps {
    task: Task;
    isAccepted?: boolean;
    onAccept?: (taskId: number) => void;
    onComplete?: (taskId: number) => void;
    onIgnore?: (taskId: number) => void;
}

const getUrgencyBadge = (urgency: number) => {
    if (urgency >= 3) {
        return {
            variant: 'error' as const,
            icon: <AlertTriangle size={12} />,
            label: '高優先度',
        };
    }
    if (urgency >= 2) {
        return {
            variant: 'warning' as const,
            icon: <AlertCircle size={12} />,
            label: '中優先度',
        };
    }
    return {
        variant: 'success' as const,
        icon: <Circle size={12} />,
        label: '低優先度',
    };
};

export default function TaskCard({ task, isAccepted, onAccept, onComplete, onIgnore }: TaskCardProps) {
    const urgencyBadge = getUrgencyBadge(task.urgency ?? 2);

    return (
        <Card elevation={2} padding="medium" hoverable>
            <div className="space-y-4">
                {/* Header with title and urgency */}
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                        <h3 className="text-xl font-semibold text-[var(--gray-900)] mb-1">
                            {task.title}
                        </h3>
                        {task.location && (
                            <div className="flex items-center gap-1 text-sm text-[var(--gray-600)]">
                                <MapPin size={14} />
                                <span>{task.location}</span>
                            </div>
                        )}
                    </div>
                    <Badge variant={urgencyBadge.variant} icon={urgencyBadge.icon}>
                        {urgencyBadge.label}
                    </Badge>
                </div>

                {/* Description */}
                {task.description && (
                    <p className="text-[var(--gray-700)] leading-relaxed">
                        {task.description}
                    </p>
                )}

                <div className="flex items-center gap-3">
                    <Badge variant="gold" icon={<Coins size={14} />}>
                        {task.bounty_gold} 最適化承認スコア
                    </Badge>
                </div>

                {/* Actions */}
                {!task.is_completed && !isAccepted && (
                    <motion.div
                        className="flex gap-2 pt-2"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                    >
                        <Button
                            variant="primary"
                            size="medium"
                            onClick={() => onAccept?.(task.id)}
                            className="flex-1"
                        >
                            受諾
                        </Button>
                        <Button
                            variant="ghost"
                            size="medium"
                            onClick={() => onIgnore?.(task.id)}
                        >
                            無視
                        </Button>
                    </motion.div>
                )}

                {!task.is_completed && isAccepted && (
                    <motion.div
                        className="flex gap-2 pt-2"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                    >
                        <Badge variant="info" size="medium">
                            対応中
                        </Badge>
                        <Button
                            variant="secondary"
                            size="medium"
                            onClick={() => onComplete?.(task.id)}
                            className="flex-1"
                        >
                            完了
                        </Button>
                    </motion.div>
                )}

                {task.is_completed && (
                    <div className="pt-2">
                        <Badge variant="success" size="medium">
                            ✓ 完了済み
                        </Badge>
                    </div>
                )}
            </div>
        </Card>
    );
}
