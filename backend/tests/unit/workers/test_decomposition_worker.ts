import { DecompositionWorker } from '../../../src/workers/decomposition_worker';
import { GoalRepository } from '../../../src/models/goal_model';
import { TaskRepository } from '../../../src/models/task_model';
import { PlannerAgent } from '../../../src/agents/planner_agent';

// Mock repositories and agents
const mockGoalRepo = {
  findById: jest.fn(),
  updateState: jest.fn(),
} as unknown as GoalRepository;

const mockTaskRepo = {
  createMany: jest.fn(),
} as unknown as TaskRepository;

const mockPlannerAgent = {
  run: jest.fn(),
  parseTasks: jest.fn(),
} as unknown as PlannerAgent;

describe('DecompositionWorker', () => {
  let decompositionWorker: DecompositionWorker;

  beforeEach(() => {
    jest.clearAllMocks();
    decompositionWorker = new DecompositionWorker(mockGoalRepo, mockTaskRepo, mockPlannerAgent);
  });

  it('should process a decomposition job', async () => {
    const goalId = 'goal-123';
    const goal = { id: goalId, title: 'Test Goal', description: 'Test Description' };
    (mockGoalRepo.findById as jest.Mock).mockResolvedValue(goal);
    (mockPlannerAgent.run as jest.Mock).mockResolvedValue({ content: '{"tasks": []}' });
    (mockPlannerAgent.parseTasks as jest.Mock).mockReturnValue([
      { title: 'Task 1', description: 'Desc 1', order: 0, dependsOn: [] },
    ]);

    await decompositionWorker.process({ data: { goalId } } as any);

    expect(mockGoalRepo.findById).toHaveBeenCalledWith(goalId);
    expect(mockPlannerAgent.run).toHaveBeenCalled();
    expect(mockTaskRepo.createMany).toHaveBeenCalled();
    expect(mockGoalRepo.updateState).toHaveBeenCalledWith(goalId, 'PENDING_APPROVAL');
  });
});
