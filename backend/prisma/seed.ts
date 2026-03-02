/**
 * Database Seed Script
 * Initializes the SystemState singleton and optional seed data
 */

import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting database seed...');

  // Seed SystemState singleton
  const systemState = await prisma.systemState.upsert({
    where: { id: 'system-state-singleton' },
    update: {},
    create: {
      id: 'system-state-singleton',
      state: 'Idle',
      lastActivity: new Date(),
    },
  });

  console.log('✓ SystemState initialized:', systemState.state);

  // Optional: Seed some sample tasks for development
  const sampleTasks = [
    {
      title: 'Learn the API',
      description: 'Explore all endpoints and understand the system',
      status: 'Pending',
    },
    {
      title: 'Create documentation',
      description: 'Write comprehensive API documentation',
      status: 'Pending',
    },
  ];

  for (const taskData of sampleTasks) {
    await prisma.task.upsert({
      where: { id: `seed-task-${taskData.title.toLowerCase().replace(/\s+/g, '-')}` },
      update: {},
      create: {
        id: `seed-task-${taskData.title.toLowerCase().replace(/\s+/g, '-')}`,
        ...taskData,
      },
    });
    console.log(`✓ Task seeded: ${taskData.title}`);
  }

  console.log('🎉 Database seed completed successfully!');
}

main()
  .catch((e) => {
    console.error('❌ Seed error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
