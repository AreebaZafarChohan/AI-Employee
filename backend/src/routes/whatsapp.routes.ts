/**
 * WhatsApp Routes
 * Defines all WhatsApp-related endpoints
 */

import { Router } from 'express';
import { whatsappController } from '../controllers/whatsapp.controller';

const router = Router();

/**
 * @route   GET /api/v1/whatsapp/messages
 * @desc    Get WhatsApp messages with pagination
 * @access  Public
 */
router.get('/messages', whatsappController.getMessages.bind(whatsappController));

/**
 * @route   GET /api/v1/whatsapp/pending
 * @desc    Get pending WhatsApp messages
 */
router.get('/pending', whatsappController.getPending.bind(whatsappController));

/**
 * @route   GET /api/v1/whatsapp/contacts
 * @desc    Get WhatsApp contacts
 */
router.get('/contacts', whatsappController.getContacts.bind(whatsappController));

/**
 * @route   POST /api/v1/whatsapp/send
 * @desc    Send a WhatsApp message
 */
router.post('/send', whatsappController.sendMessage.bind(whatsappController));

/**
 * @route   POST /api/v1/whatsapp/approve
 * @desc    Approve a pending message
 */
router.post('/approve', whatsappController.approveMessage.bind(whatsappController));

/**
 * @route   POST /api/v1/whatsapp/reject
 * @desc    Reject a pending message
 */
router.post('/reject', whatsappController.rejectMessage.bind(whatsappController));

/**
 * @route   GET /api/v1/whatsapp/status
 * @desc    Get WhatsApp service status
 */
router.get('/status', whatsappController.getStatus.bind(whatsappController));

export default router;
