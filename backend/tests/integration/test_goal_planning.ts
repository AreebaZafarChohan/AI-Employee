import request from 'supertest';
import { createApp } from '../../src/app';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const app = createApp();

describe('Goal Planning Integration', () => {
  beforeAll(async () => {
    // Clean up test data
    await prisma.task.deleteMany();
    await prisma.goal.deleteMany();
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  it('should go through the full goal planning workflow', async () => {
    // 1. Submit Goal
    const submitRes = await request(app)
      .post('/api/v1/goals')
      .send({
        title: 'Integration Test Goal',
        description: 'Test decomposition and approval',
      });

    expect(submitRes.status).toBe(201);
    const goalId = submitRes.body.id;
    expect(goalId).toBeDefined();

    // 2. Wait for decomposition (Simulated)
    // In a real integration test with workers, we'd need to wait or mock the worker.
    // For now, we'll manually create tasks to simulate decomposition success.
    await prisma.task.create({
      data: {
        goalId,
        title: 'Subtask 1',
        description: 'First subtask',
        order: 0,
        status: 'PENDING',
      }
    });

    await prisma.goal.update({
      where: { id: goalId },
      data: { state: 'PENDING_APPROVAL' }
    });

    // 3. Get Plan
    const planRes = await request(app).get(`/api/v1/goals/${goalId}/plan`);
    expect(planRes.status).toBe(200);
    expect(planRes.body.tasks.length).toBeGreaterThan(0);

    // 4. Approve Plan
    const approveRes = await request(app)
      .post(`/api/v1/goals/${goalId}/plan`)
      .send({ action: 'APPROVE' });

    expect(approveRes.status).toBe(200);
    expect(approveRes.body.goal.state).toBe('ACTIVE');

    // 5. Verify final status
    const statusRes = await request(app).get(`/api/v1/goals/${goalId}`);
    expect(statusRes.body.state).toBe('ACTIVE');
  });
});
