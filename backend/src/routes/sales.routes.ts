/**
 * Sales Routes
 * Defines all sales pipeline endpoints
 */

import { Router } from 'express';
import { salesController } from '../controllers/sales.controller';

const router = Router();

router.get('/leads', salesController.getLeads.bind(salesController));
router.get('/leads/:id', salesController.getLeadById.bind(salesController));
router.get('/pipeline', salesController.getPipelineStats.bind(salesController));
router.post('/discover', salesController.triggerDiscovery.bind(salesController));
router.get('/invoices', salesController.getInvoices.bind(salesController));
router.get('/payments', salesController.getPaymentStatus.bind(salesController));

export default router;
