'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Plan } from '@/types/plan';
import { cn } from '@/lib/utils';
import { FileText, ChevronRight } from 'lucide-react';

interface PlanDisplayProps {
  plan: Plan;
  className?: string;
}

export function PlanDisplay({ plan, className }: PlanDisplayProps) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">Generated Plan</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        <div className="p-3 bg-muted rounded-lg">
          <p className="text-sm text-muted-foreground">{plan.summary}</p>
        </div>

        {/* Sections */}
        <div className="space-y-3">
          {plan.sections.map((section, index) => (
            <div key={index} className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  Section {index + 1}
                </Badge>
                <h4 className="text-sm font-semibold">{section.title}</h4>
              </div>
              <ul className="space-y-1 ml-4">
                {section.steps.map((step, stepIndex) => (
                  <li key={stepIndex} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <ChevronRight className="h-4 w-4 mt-0.5 flex-shrink-0 text-primary" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Footer */}
        <p className="text-xs text-muted-foreground pt-2 border-t">
          Created {new Date(plan.createdAt).toLocaleString()}
        </p>
      </CardContent>
    </Card>
  );
}
