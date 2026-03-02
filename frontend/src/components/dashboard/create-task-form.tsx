'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useCreateTask } from '@/hooks/use-tasks';
import { useToast } from '@/components/ui/use-toast';
import { Plus, Loader2 } from 'lucide-react';

interface CreateTaskFormProps {
  onSuccess?: () => void;
}

export function CreateTaskForm({ onSuccess }: CreateTaskFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const { mutateAsync: createTask, isPending } = useCreateTask();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      toast({
        title: 'Title required',
        description: 'Please enter a task title',
        variant: 'error',
      });
      return;
    }

    try {
      await createTask({
        title: title.trim(),
        description: description.trim() || undefined,
      });
      
      toast({
        title: 'Task created',
        description: 'Your task has been saved successfully',
        variant: 'success',
      });

      // Reset form
      setTitle('');
      setDescription('');
      setIsOpen(false);
      
      // Notify parent to refresh
      onSuccess?.();
    } catch (err) {
      toast({
        title: 'Failed to create task',
        description: err instanceof Error ? err.message : 'Please try again',
        variant: 'error',
      });
    }
  };

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        className="w-full"
        variant="outline"
      >
        <Plus className="h-4 w-4 mr-2" />
        Create Task
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Create New Task</CardTitle>
        <CardDescription>
          Add a new task to your list
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">
              Title <span className="text-destructive">*</span>
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done?"
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
              disabled={isPending}
            />
          </div>
          
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more details (optional)"
              rows={3}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
              disabled={isPending}
            />
          </div>

          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={isPending}
              className="flex-1"
            >
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Task'
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
