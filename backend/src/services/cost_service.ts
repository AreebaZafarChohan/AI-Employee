import { getEncoding } from 'js-tiktoken';
import { CostRepository } from '../models/cost_model';
import { logger } from '../lib/logger';
import { Decimal } from 'decimal.js';

const enc = getEncoding('cl100k_base');

export class CostMonitoringService {
  private costRepo: CostRepository;

  constructor(costRepo: CostRepository = new CostRepository()) {
    this.costRepo = costRepo;
  }

  async estimateAndLog(agentExecutionId: string | undefined, modelName: string, prompt: string, completion: string) {
    const tokensIn = enc.encode(prompt).length;
    const tokensOut = enc.encode(completion).length;

    // Simulated pricing: $0.03 / 1k tokens in, $0.06 / 1k tokens out (GPT-4)
    const costIn = (tokensIn / 1000) * 0.03;
    const costOut = (tokensOut / 1000) * 0.06;
    const totalCost = costIn + costOut;

    logger.info(`Cost Logged: ${totalCost.toFixed(4)} USD for ${modelName}`);

    await this.costRepo.create({
      agentExecutionId,
      modelName,
      tokensIn,
      tokensOut,
      estimatedCostUsd: totalCost,
    });

    // Check threshold
    await this.checkThreshold();
  }

  async checkThreshold() {
    const totalCost = await this.costRepo.getTotalCost();
    const threshold = await this.costRepo.getThreshold();

    if (threshold > 0 && totalCost.greaterThan(new Decimal(threshold))) {
      logger.warn(`COST THRESHOLD EXCEEDED: ${totalCost.toFixed(2)} USD > ${threshold.toFixed(2)} USD`);
      // In a real app, this would trigger an alert or pause execution via a service call
      return true;
    }
    return false;
  }

  async setThreshold(threshold: number) {
    return await this.costRepo.setThreshold(threshold);
  }

  async getStatus() {
    const totalCost = await this.costRepo.getTotalCost();
    const threshold = await this.costRepo.getThreshold();
    return {
      totalCost: totalCost.toNumber(),
      threshold,
      isExceeded: threshold > 0 && totalCost.greaterThan(new Decimal(threshold)),
    };
  }
}
