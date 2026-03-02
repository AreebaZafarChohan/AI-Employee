'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { usePlans } from '@/hooks/use-plans';
import { useTasks } from '@/hooks/use-tasks';
import { useToast } from '@/components/ui/use-toast';
import { Sparkles, Loader2, RefreshCw } from 'lucide-react';
import type { Plan } from '@/types/plan';

interface PlanGeneratorProps {
  onPlanGenerated?: (plan: Plan) => void;
}

export function PlanGenerator({ onPlanGenerated }: PlanGeneratorProps) {
  const { tasks } = useTasks();
  const { generatePlan, isGenerating, error } = usePlans();
  const { toast } = useToast();
  const [lastPlan, setLastPlan] = useState<Plan | null>(null);

  const handleGeneratePlan = async () => {
    if (tasks.length === 0) {
      toast({
        title: 'No tasks available',
        description: 'Create some tasks before generating a plan',
        variant: 'warning',
      });
      return;
    }

    try {
      const result = await generatePlan({ taskIds: tasks.map((t) => t.id) });
      
      // Check if result is a plan or a status
      if ('sections' in result) {
        setLastPlan(result);
        onPlanGenerated?.(result);
        
        toast({
          title: 'Plan generated',
          description: 'AI has created a structured plan for your tasks',
          variant: 'success',
        });
      } else {
        // It's a processing status
        toast({
          title: 'Plan in progress',
          description: 'AI is working on your plan. Please check back soon.',
          variant: 'info',
        });
      }
    } catch (err) {
      toast({
        title: 'Failed to generate plan',
        description: err instanceof Error ? err.message : 'Please try again',
        variant: 'error',
      });
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">AI Plan Generator</CardTitle>
          </div>
          {lastPlan && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleGeneratePlan}
              disabled={isGenerating}
            >
              <RefreshCw className="h-4 w-4 mr-1" />
              Regenerate
            </Button>
          )}
        </div>
        <CardDescription>
          Generate a structured plan for your {tasks.length} task{tasks.length !== 1 ? 's' : ''}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button
          onClick={handleGeneratePlan}
          disabled={isGenerating || tasks.length === 0}
          className="w-full"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Thinking...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Generate Plan
            </>
          )}
        </Button>
        
        {error && (
          <p className="text-sm text-destructive mt-2">
            {error.message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
