import { GoalService } from '../../../src/services/goal_service';
import { GoalRepository } from '../../../src/models/goal_model';
import { TaskRepository } from '../../../src/models/task_model';

// Mock repositories
const mockGoalRepo = {
  create: jest.fn(),
  findById: jest.fn(),
  updateState: jest.fn(),
} as unknown as GoalRepository;

const mockTaskRepo = {
  createMany: jest.fn(),
  findByGoalId: jest.fn(),
} as unknown as TaskRepository;

describe('GoalService', () => {
  let goalService: GoalService;

  beforeEach(() => {
    jest.clearAllMocks();
    goalService = new GoalService(mockGoalRepo, mockTaskRepo);
  });

  it('should create a goal and add to queue', async () => {
    const goalData = { title: 'Test Goal', description: 'Test Description' };
    (mockGoalRepo.create as jest.Mock).mockResolvedValue({ id: 'goal-123', ...goalData });

    const result = await goalService.submitGoal(goalData);

    expect(mockGoalRepo.create).toHaveBeenCalledWith(goalData);
    expect(result.id).toBe('goal-123');
  });

  it('should approve a plan and update goal state', async () => {
    const goalId = 'goal-123';
    (mockGoalRepo.updateState as jest.Mock).mockResolvedValue({ id: goalId, state: 'ACTIVE' });
    (mockTaskRepo.findByGoalId as jest.Mock).mockResolvedValue([]);

    const result = await goalService.approvePlan(goalId);

    expect(mockGoalRepo.updateState).toHaveBeenCalledWith(goalId, 'ACTIVE');
    expect(result.state).toBe('ACTIVE');
  });
});
