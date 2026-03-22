'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import type { CreateGoalInput } from '@/hooks/use-goals';

interface GoalFormProps {
  onSubmit: (data: CreateGoalInput) => void;
  onCancel?: () => void;
  isLoading?: boolean;
}

export function GoalForm({ onSubmit, onCancel, isLoading }: GoalFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<CreateGoalInput['priority']>('medium');
  const [error, setError] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    setError('');
    onSubmit({ title: title.trim(), description: description.trim(), priority });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="goal-title" className="block text-sm font-medium mb-1">
          Title
        </label>
        <Input
          id="goal-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Goal title"
        />
        {error && <p className="text-sm text-destructive mt-1">{error}</p>}
      </div>

      <div>
        <label htmlFor="goal-description" className="block text-sm font-medium mb-1">
          Description
        </label>
        <Textarea
          id="goal-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the goal..."
          rows={3}
        />
      </div>

      <div>
        <label htmlFor="goal-priority" className="block text-sm font-medium mb-1">
          Priority
        </label>
        <select
          id="goal-priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as CreateGoalInput['priority'])}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
      </div>

      <div className="flex gap-2 justify-end">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Creating...' : 'Create Goal'}
        </Button>
      </div>
    </form>
  );
}
