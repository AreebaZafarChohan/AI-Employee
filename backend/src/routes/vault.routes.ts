/**
 * Vault Routes
 * Defines endpoints for vault management (Needs_Action, Pending, Approved, etc.)
 */

import { Router } from 'express';
import { vaultController } from '../controllers/vault.controller';

const router = Router();

router.get('/needs-action', vaultController.getNeedsAction.bind(vaultController));
router.get('/pending', vaultController.getPending.bind(vaultController));
router.get('/approved', vaultController.getApproved.bind(vaultController));
router.get('/rejected', vaultController.getRejected.bind(vaultController));
router.get('/done', vaultController.getDone.bind(vaultController));
router.get('/counts', vaultController.getCounts.bind(vaultController));

router.post('/approve', vaultController.approve.bind(vaultController));
router.post('/reject', vaultController.reject.bind(vaultController));

export default router;
