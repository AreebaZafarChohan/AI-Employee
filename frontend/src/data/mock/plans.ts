import { Plan } from '../types/plan';

export const MOCK_PLANS: Plan[] = [
  {
    id: 'plan-001',
    title: 'Q1 Marketing Strategy',
    status: 'Ready',
    createdAt: new Date('2026-02-15T09:00:00Z'),
    description: 'Comprehensive marketing plan for Q1 2026',
    updatedAt: new Date('2026-02-18T14:30:00Z')
  },
  {
    id: 'plan-002',
    title: 'Product Launch Timeline',
    status: 'Draft',
    createdAt: new Date('2026-02-20T11:00:00Z'),
    description: 'Timeline and milestones for new product launch'
  },
  {
    id: 'plan-003',
    title: 'Customer Feedback Analysis',
    status: 'Done',
    createdAt: new Date('2026-02-10T08:00:00Z'),
    description: 'Analysis of customer feedback from January survey',
    completedAt: new Date('2026-02-12T16:00:00Z')
  },
  {
    id: 'plan-004',
    title: 'Website Redesign',
    status: 'Ready',
    createdAt: new Date('2026-02-18T10:00:00Z'),
    description: 'Complete overhaul of company website with modern design'
  },
  {
    id: 'plan-005',
    title: 'Employee Training Program',
    status: 'Draft',
    createdAt: new Date('2026-02-21T08:00:00Z'),
    description: 'Training program for new employee onboarding'
  }
];

/**
 * Get all plans (mock implementation)
 * @returns Promise resolving to array of plans
 */
export async function getPlans(): Promise<Plan[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_PLANS;
}

/**
 * Get plan by ID (mock implementation)
 * @param id - Plan ID to retrieve
 * @returns Promise resolving to plan or undefined
 */
export async function getPlanById(id: string): Promise<Plan | undefined> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_PLANS.find(plan => plan.id === id);
}

/**
 * Get plans by status (mock implementation)
 * @param status - Plan status to filter by
 * @returns Promise resolving to filtered array of plans
 */
export async function getPlansByStatus(status: Plan['status']): Promise<Plan[]> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_PLANS.filter(plan => plan.status === status);
}
